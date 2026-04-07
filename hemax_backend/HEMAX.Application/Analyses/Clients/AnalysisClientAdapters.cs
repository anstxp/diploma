using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Enums;

namespace HEMAX.Application.Analyses.Clients;

public sealed class CbcAnalysisClient : IHemaxAnalysisClient
{
    private readonly IHemaxCbcClient _inner;
    public CbcAnalysisClient(IHemaxCbcClient inner) { _inner = inner; }
    public AnalysisType Type => AnalysisType.Cbc;

    public Task<object> AnalyzeAsync(string payloadJson, string? language, CancellationToken ct) =>
        !string.IsNullOrEmpty(language)
            ? _inner.AnalyzeNarrativeAsync(payloadJson, language, ct)
            : _inner.AnalyzeAsync(payloadJson, ct);
}

public sealed class ChemAnalysisClient : IHemaxAnalysisClient
{
    private readonly IHemaxChemClient _inner;
    public ChemAnalysisClient(IHemaxChemClient inner) { _inner = inner; }
    public AnalysisType Type => AnalysisType.Chem;

    public Task<object> AnalyzeAsync(string payloadJson, string? language, CancellationToken ct) =>
        !string.IsNullOrEmpty(language)
            ? _inner.AnalyzeNarrativeAsync(payloadJson, language, ct)
            : _inner.AnalyzeAsync(payloadJson, ct);
}

public sealed class RiskAnalysisClient : IHemaxAnalysisClient
{
    private readonly IHemaxRiskClient _inner;
    public RiskAnalysisClient(IHemaxRiskClient inner) { _inner = inner; }
    public AnalysisType Type => AnalysisType.Risk;

    public Task<object> AnalyzeAsync(string payloadJson, string? language, CancellationToken ct) =>
        !string.IsNullOrEmpty(language)
            ? _inner.AnalyzeNarrativeAsync(payloadJson, language, ct)
            : _inner.AnalyzeAsync(payloadJson, ct);
}

public sealed class NeuroAnalysisClient : IHemaxAnalysisClient
{
    private readonly IHemaxNeuroClient _inner;
    public NeuroAnalysisClient(IHemaxNeuroClient inner) { _inner = inner; }
    public AnalysisType Type => AnalysisType.Neuro;

    public Task<object> AnalyzeAsync(string payloadJson, string? language, CancellationToken ct) =>
        !string.IsNullOrEmpty(language)
            ? _inner.AnalyzeNarrativeAsync(payloadJson, language, ct)
            : _inner.AnalyzeAsync(payloadJson, ct);
}
