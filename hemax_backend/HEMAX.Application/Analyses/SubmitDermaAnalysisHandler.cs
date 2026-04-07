using System.Text.Json;
using AutoMapper;
using HEMAX.Application.Analyses.Severity;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using HEMAX.Infrastructure.Files;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Analyses;

public class SubmitDermaAnalysisHandler : IRequestHandler<SubmitDermaAnalysisCommand, AnalysisDto>
{
    private const long MaxDermaImageBytes = 10 * 1024 * 1024; // 10 MB

    private readonly IHemaxDbContext _db;
    private readonly IHemaxApiFacade _hemax;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;
    private readonly IMapper _mapper;
    private readonly IFileStorageService _storage;
    private readonly IFileUrlGenerator _urls;
    private readonly IFileSignatureValidator _signatures;
    private readonly ISeverityExtractorRegistry _severity;

    public SubmitDermaAnalysisHandler(
        IHemaxDbContext db, IHemaxApiFacade hemax,
        ICurrentUserService current, IAuditService audit, IMapper mapper,
        IFileStorageService storage, IFileUrlGenerator urls,
        IFileSignatureValidator signatures,
        ISeverityExtractorRegistry severity)
    {
        _db = db; _hemax = hemax; _current = current;
        _audit = audit; _mapper = mapper;
        _storage = storage; _urls = urls; _signatures = signatures;
        _severity = severity;
    }

    public async Task<AnalysisDto> Handle(SubmitDermaAnalysisCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        byte[] imageBytes;
        using (var initial = new MemoryStream())
        {
            await cmd.ImageStream.CopyToAsync(initial, ct);
            imageBytes = initial.ToArray();
        }

        // Magic-byte validation
        using (var verifyStream = new MemoryStream(imageBytes, writable: false))
        {
            await _signatures.ValidateAsync(
                verifyStream, cmd.ImageContentType, FileKind.Image,
                maxBytes: MaxDermaImageBytes, ct: ct);
        }

        // Forward to ML service.
        object resultRaw;
        using (var mlStream = new MemoryStream(imageBytes, writable: false))
        {
            resultRaw = await _hemax.Derma.AnalyzeAsync(
                mlStream, cmd.ImageFileName, cmd.ImageContentType,
                cmd.Age, cmd.Sex, cmd.Localization, cmd.TopK, ct);
        }

        var resultJson = JsonSerializer.Serialize(resultRaw);

        var (severity, topFlag, _) = _severity.Extract(resultJson, AnalysisType.Derma);

        var rawInput = JsonSerializer.Serialize(new
        {
            fileName     = cmd.ImageFileName,
            contentType  = cmd.ImageContentType,
            age          = cmd.Age,
            sex          = cmd.Sex,
            localization = cmd.Localization,
        });

        var analysis = new Analysis
        {
            UserId       = _current.UserId.Value,
            Type         = AnalysisType.Derma,
            RawInputJson = rawInput,
            ResultJson   = resultJson,
            TopFlag      = topFlag,
            Severity     = severity,
            // Bug fix May 2026: persist the requested language so the UI's
            // i18n layer knows which locale this analysis was filed in.
            // DERMA Python doesn't render narrative so we don't forward this
            // to the analyzer, but the Analysis row should still record it.
            Language     = cmd.Language,
        };
        _db.Analyses.Add(analysis);
        await _db.SaveChangesAsync(ct);  // assign analysis.Id before storing FK

        try
        {
            using var blobStream = new MemoryStream(imageBytes, writable: false);
            var (storageKey, _) = await _storage.SaveAsync(
                blobStream, cmd.ImageFileName, cmd.ImageContentType, ct);

            _db.FileAssets.Add(new FileAsset
            {
                OwnerId         = _current.UserId.Value,
                Type            = FileAssetType.LesionImage,
                FileName        = cmd.ImageFileName,
                ContentType     = cmd.ImageContentType,
                SizeBytes       = imageBytes.Length,
                StorageKey      = storageKey,
                PublicUrl       = null,
                RelatedEntityId = analysis.Id,
            });
            await _db.SaveChangesAsync(ct);
        }
        catch (Exception ex)
        {
            await _audit.LogAsync(AuditAction.AnalysisSubmitted, "Analysis", analysis.Id,
                new { type = "Derma", error = "image_storage_failed", message = ex.Message }, ct);
        }

        await _audit.LogAsync(AuditAction.AnalysisSubmitted, "Analysis", analysis.Id,
            new { type = "Derma", topClass = topFlag, severity }, ct);

        return await BuildDtoWithFileAsync(analysis, ct);
    }

    private async Task<AnalysisDto> BuildDtoWithFileAsync(Analysis analysis, CancellationToken ct)
    {
        var dto = _mapper.Map<AnalysisDto>(analysis);
        var file = await _db.FileAssets
            .Where(f => f.RelatedEntityId == analysis.Id
                     && (f.Type == FileAssetType.LesionImage || f.Type == FileAssetType.PdfReport))
            .OrderByDescending(f => f.CreatedAt)
            .FirstOrDefaultAsync(ct);
        if (file == null) return dto;

        var url = _urls.GetDownloadUrl(file.StorageKey);
        return dto with { FileUrl = url, FileName = file.FileName };
    }
}
