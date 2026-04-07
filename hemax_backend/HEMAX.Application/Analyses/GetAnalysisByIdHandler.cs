using AutoMapper;
using HEMAX.Application.Analyses.Clients;
using HEMAX.Application.Analyses.Severity;
using HEMAX.Application.Common;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using HEMAX.Infrastructure.Files;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace HEMAX.Application.Analyses;

public class GetAnalysisByIdHandler : IRequestHandler<GetAnalysisByIdQuery, AnalysisDetailDto>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IMapper _mapper;
    private readonly IFileUrlGenerator _urls;
    private readonly IHemaxAnalysisClientRegistry _clients;
    private readonly ISeverityExtractorRegistry _severity;
    private readonly ILogger<GetAnalysisByIdHandler> _logger;

    public GetAnalysisByIdHandler(
        IHemaxDbContext db, ICurrentUserService current, IMapper mapper,
        IFileUrlGenerator urls,
        IHemaxAnalysisClientRegistry clients,
        ISeverityExtractorRegistry severity,
        ILogger<GetAnalysisByIdHandler> logger)
    {
        _db = db; _current = current; _mapper = mapper; _urls = urls;
        _clients = clients; _severity = severity; _logger = logger;
    }

    public async Task<AnalysisDetailDto> Handle(GetAnalysisByIdQuery q, CancellationToken ct)
    {
        var a = await _db.Analyses.FirstOrDefaultAsync(x => x.Id == q.Id, ct)
            ?? throw new EntityNotFoundException("Analysis", q.Id);

        await AuthorizationGuard.EnsureCanViewUserDataAsync(_db, _current, a.UserId, ct);

        var dto = _mapper.Map<AnalysisDetailDto>(a);

        var requestedLang = q.Language?.ToLowerInvariant();
        var storedLang    = string.IsNullOrEmpty(a.Language) ? "uk" : a.Language.ToLowerInvariant();

        if (!string.IsNullOrEmpty(requestedLang)
            && requestedLang != storedLang
            && a.Type != AnalysisType.Derma)
        {
            try
            {
                var client = _clients.For(a.Type);
                var resultRaw = await client.AnalyzeAsync(a.RawInputJson, requestedLang, ct);
                var resultJson = JsonSerializer.Serialize(resultRaw);

                var (severity, topFlag, summary) = _severity.Extract(resultJson, a.Type);

                dto = dto with
                {
                    ResultJson = resultJson,
                    TopFlag    = topFlag,
                    SummaryUa  = summary,
                    Severity   = severity,
                    Language   = requestedLang,
                };

                _logger.LogInformation(
                    "Re-rendered analysis {Id} ({Type}) from {Stored} to {Requested}",
                    a.Id, a.Type, storedLang, requestedLang);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex,
                    "Failed to re-render analysis {Id} from {Stored} to {Requested}, " +
                    "returning stored result instead.",
                    a.Id, storedLang, requestedLang);
            }
        }

        var file = await _db.FileAssets
            .Where(f => f.RelatedEntityId == a.Id
                     && (f.Type == FileAssetType.LesionImage || f.Type == FileAssetType.PdfReport))
            .OrderByDescending(f => f.CreatedAt)
            .FirstOrDefaultAsync(ct);

        return file is null
            ? dto
            : dto with { FileUrl = _urls.GetDownloadUrl(file.StorageKey), FileName = file.FileName };
    }
}
