using HEMAX.Application.Analyses.Clients;
using HEMAX.Application.Analyses.Context;
using HEMAX.Application.Analyses.Severity;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using AutoMapper;
using MediatR;
using System.Text.Json;
using HEMAX.Domain.Exceptions;

namespace HEMAX.Application.Analyses;

public class SubmitAnalysisHandler : IRequestHandler<SubmitAnalysisCommand, AnalysisDto>
{
    private readonly IHemaxDbContext _db;
    private readonly IHemaxAnalysisClientRegistry _clients;
    private readonly ISeverityExtractorRegistry _severity;
    private readonly IPatientContextBuilder _context;
    private readonly IRecentLabsMerger _labsMerger;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;
    private readonly IMapper _mapper;

    public SubmitAnalysisHandler(
        IHemaxDbContext db,
        IHemaxAnalysisClientRegistry clients,
        ISeverityExtractorRegistry severity,
        IPatientContextBuilder context,
        IRecentLabsMerger labsMerger,
        ICurrentUserService current,
        IAuditService audit,
        IMapper mapper)
    {
        _db = db; _clients = clients; _severity = severity;
        _context = context; _labsMerger = labsMerger;
        _current = current; _audit = audit; _mapper = mapper;
    }

    public async Task<AnalysisDto> Handle(SubmitAnalysisCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        if (cmd.Type == AnalysisType.Derma)
            throw new BusinessRuleViolationException(
                "USE_DERMA_ENDPOINT", "Use POST /api/analyses/derma for image upload");

        var payloadJson = cmd.PayloadJson;

        if (cmd.MergeRecentLabs)
            payloadJson = await _labsMerger.MergeAsync(payloadJson, _current.UserId.Value, ct);

        payloadJson = await _context.InjectContextAsync(payloadJson, _current.UserId.Value, ct);

        if (cmd.Type == AnalysisType.Chem)
            payloadJson = ChemPayloadNormalizer.Normalize(payloadJson);

        if (cmd.Type == AnalysisType.Risk || cmd.Type == AnalysisType.Neuro)
            payloadJson = LabUnitConverter.NormalizePayloadLabs(payloadJson);

        var client = _clients.For(cmd.Type);
        var resultRaw = await client.AnalyzeAsync(payloadJson, cmd.Language, ct);
        var resultJson = JsonSerializer.Serialize(resultRaw);

        var (severity, topFlag, summary) = _severity.Extract(resultJson, cmd.Type);

        // Step 5: persist.
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

        await _audit.LogAsync(AuditAction.AnalysisSubmitted, "Analysis", analysis.Id,
            new { type = cmd.Type.ToString(), severity }, ct);

        return _mapper.Map<AnalysisDto>(analysis);
    }
}
