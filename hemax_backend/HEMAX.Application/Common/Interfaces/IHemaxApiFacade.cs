
namespace HEMAX.Application.Common.Interfaces;

public interface IHemaxApiFacade
{
    IHemaxCbcClient   Cbc   { get; }
    IHemaxChemClient  Chem  { get; }
    IHemaxRiskClient  Risk  { get; }
    IHemaxNeuroClient Neuro { get; }
    IHemaxDermaClient Derma { get; }
}

// Forward-declarations of the per-service interfaces.
// These are the same as in csharp_*.zip bundles; import the actual interfaces
// from the Infrastructure layer.
//
// Language plumbing fix (May 2026):
//   AnalyzeNarrativeAsync now accepts an explicit `lang` parameter.
//   Implementations inject it into the JSON body as `{ ..., "lang": "uk" | "en" }`
//   so the Python NarrativeRequest model picks it up (it defaults to "uk"
//   when missing — that was the bug; the .NET layer was dropping the value).

public interface IHemaxCbcClient
{
    Task<bool> IsHealthyAsync(CancellationToken ct = default);
    Task<object> AnalyzeAsync(object request, CancellationToken ct = default);
    Task<object> AnalyzeNarrativeAsync(object request, string? lang, CancellationToken ct = default);
}

public interface IHemaxChemClient
{
    Task<bool> IsHealthyAsync(CancellationToken ct = default);
    Task<object> AnalyzeAsync(object request, CancellationToken ct = default);
    Task<object> AnalyzeNarrativeAsync(object request, string? lang, CancellationToken ct = default);
}

public interface IHemaxRiskClient
{
    Task<bool> IsHealthyAsync(CancellationToken ct = default);
    Task<object> AnalyzeAsync(object request, CancellationToken ct = default);
    Task<object> AnalyzeNarrativeAsync(object request, string? lang, CancellationToken ct = default);
}

public interface IHemaxNeuroClient
{
    Task<bool> IsHealthyAsync(CancellationToken ct = default);
    Task<object> AnalyzeAsync(object request, CancellationToken ct = default);
    Task<object> AnalyzeNarrativeAsync(object request, string? lang, CancellationToken ct = default);
}

public interface IHemaxDermaClient
{
    Task<bool> IsHealthyAsync(CancellationToken ct = default);
    Task<object> AnalyzeAsync(
        Stream imageStream, string fileName, string contentType,
        double? age = null, string? sex = null, string? localization = null,
        int topK = 3, CancellationToken ct = default);
}
