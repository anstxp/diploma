using System.Linq;
using System.Text.Json;
using AutoMapper;
using HEMAX.Application.Analyses.Context;
using HEMAX.Application.Analyses.Severity;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using HEMAX.Infrastructure.Files;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Analyses;


public class ExtractFromPdfHandler : IRequestHandler<ExtractFromPdfCommand, PdfExtractionDto>
{
    private const long MaxPdfBytes = 25 * 1024 * 1024; // 25 MB

    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IFileStorageService _storage;
    private readonly IFileUrlGenerator _urls;
    private readonly IPdfLabReportParser _parser;
    private readonly IAuditService _audit;
    private readonly IFileSignatureValidator _signatures;

    public ExtractFromPdfHandler(
        IHemaxDbContext db, ICurrentUserService current,
        IFileStorageService storage, IFileUrlGenerator urls,
        IPdfLabReportParser parser, IAuditService audit,
        IFileSignatureValidator signatures)
    {
        _db = db; _current = current;
        _storage = storage; _urls = urls;
        _parser = parser; _audit = audit;
        _signatures = signatures;
    }

    public async Task<PdfExtractionDto> Handle(ExtractFromPdfCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        using var ms = new MemoryStream();
        await cmd.PdfStream.CopyToAsync(ms, ct);
        ms.Position = 0;

        await _signatures.ValidateAsync(
            ms, cmd.ContentType, FileKind.Pdf,
            maxBytes: MaxPdfBytes, ct: ct);
        ms.Position = 0;

        // Parse first
        var extraction = await _parser.ParseAsync(ms, cmd.Hint, ct);

        // Save PDF to blob storage
        ms.Position = 0;
        var (storageKey, _) = await _storage.SaveAsync(
            ms, cmd.FileName, cmd.ContentType, ct,
            category: "pdfs");

        var fileAsset = new FileAsset
        {
            OwnerId         = _current.UserId.Value,
            Type            = FileAssetType.PdfReport,
            FileName        = cmd.FileName,
            ContentType     = cmd.ContentType,
            SizeBytes       = ms.Length,
            StorageKey      = storageKey,
            PublicUrl       = null,  // SAS generated on demand
            RelatedEntityId = null,  // not yet linked to an analysis
        };
        _db.FileAssets.Add(fileAsset);
        await _db.SaveChangesAsync(ct);

        await _audit.LogAsync(
            AuditAction.AnalysisSubmitted,
            "FileAsset", fileAsset.Id,
            new
            {
                action = "pdf_extraction",
                detectedKind = extraction.DetectedKind,
                lab = extraction.LabName,
                matchedAnalytes = extraction.Values.Count,
                confidence = extraction.Confidence,
            }, ct);

        var fileUrl = _urls.GetDownloadUrl(storageKey);

        return new PdfExtractionDto(
            DetectedKind:   extraction.DetectedKind,
            Values:         extraction.Values,
            Units:          extraction.Units,
            LabName:        extraction.LabName,
            Confidence:     extraction.Confidence,
            PdfFileAssetId: fileAsset.Id,
            PdfFileUrl:     fileUrl
        );
    }
}


public class SubmitAnalysisFromPdfHandler : IRequestHandler<SubmitAnalysisFromPdfCommand, AnalysisDto>
{
    private readonly IHemaxDbContext _db;
    private readonly IHemaxApiFacade _hemax;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;
    private readonly IMapper _mapper;
    private readonly IFileUrlGenerator _urls;
    private readonly IPatientContextBuilder _context;  // ← P3 cleanup: use shared builder
    private readonly ISeverityExtractorRegistry _severity;  // ← unify with JSON path

    public SubmitAnalysisFromPdfHandler(
        IHemaxDbContext db, IHemaxApiFacade hemax,
        ICurrentUserService current, IAuditService audit, IMapper mapper,
        IFileUrlGenerator urls,
        IPatientContextBuilder context,  // ← P3 cleanup
        ISeverityExtractorRegistry severity)  // ← unify with JSON path
    {
        _db = db; _hemax = hemax; _current = current;
        _audit = audit; _mapper = mapper; _urls = urls;
        _context = context; _severity = severity;
    }

    public async Task<AnalysisDto> Handle(SubmitAnalysisFromPdfCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        if (cmd.Type != AnalysisType.Cbc && cmd.Type != AnalysisType.Chem)
            throw new BusinessRuleViolationException("INVALID_TYPE",
                "PDF submission only supported for CBC and CHEM");

        var pdf = await _db.FileAssets.FirstOrDefaultAsync(
            f => f.Id == cmd.PdfFileAssetId
              && f.OwnerId == _current.UserId.Value
              && f.Type == FileAssetType.PdfReport, ct)
            ?? throw new EntityNotFoundException("FileAsset", cmd.PdfFileAssetId);

        var payloadJson = await _context.InjectContextAsync(cmd.PayloadJson, _current.UserId.Value, ct);

        if (cmd.Type == AnalysisType.Chem)
            payloadJson = ChemPayloadNormalizer.Normalize(payloadJson);

        var useNarrative = !string.IsNullOrEmpty(cmd.Language);
        object resultRaw = cmd.Type switch
        {
            AnalysisType.Cbc when useNarrative   => await _hemax.Cbc.AnalyzeNarrativeAsync(payloadJson, cmd.Language, ct),
            AnalysisType.Cbc                     => await _hemax.Cbc.AnalyzeAsync(payloadJson, ct),
            AnalysisType.Chem when useNarrative  => await _hemax.Chem.AnalyzeNarrativeAsync(payloadJson, cmd.Language, ct),
            AnalysisType.Chem                    => await _hemax.Chem.AnalyzeAsync(payloadJson, ct),
            _ => throw new ArgumentOutOfRangeException(nameof(cmd.Type)),
        };

        var resultJson = JsonSerializer.Serialize(resultRaw);
        var (severity, topFlag, summary) = _severity.Extract(resultJson, cmd.Type);

        var analysis = new Analysis
        {
            UserId       = _current.UserId.Value,
            Type         = cmd.Type,
            RawInputJson = payloadJson,
            ResultJson   = resultJson,
            TopFlag      = topFlag,
            Severity     = severity,
            SummaryUa    = summary,
            Language     = cmd.Language,
        };
        _db.Analyses.Add(analysis);
        await _db.SaveChangesAsync(ct);

        // Link the PDF to this analysis
        pdf.RelatedEntityId = analysis.Id;
        await _db.SaveChangesAsync(ct);

        await _audit.LogAsync(AuditAction.AnalysisSubmitted, "Analysis", analysis.Id,
            new { type = cmd.Type.ToString(), severity, source = "pdf", pdfFileAssetId = pdf.Id }, ct);

        var dto = _mapper.Map<AnalysisDto>(analysis);
        var fileUrl = _urls.GetDownloadUrl(pdf.StorageKey);
        return dto with { FileUrl = fileUrl, FileName = pdf.FileName };
    }
}
