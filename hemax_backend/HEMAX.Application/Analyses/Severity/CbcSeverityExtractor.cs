using System.Text.Json;
using HEMAX.Domain.Enums;

namespace HEMAX.Application.Analyses.Severity;

public sealed class CbcSeverityExtractor : ISeverityExtractor
{
    public AnalysisType Type => AnalysisType.Cbc;

    public (AnalysisSeverity severity, string? topFlag, string? summary) Extract(JsonElement root)
    {
        if (root.TryGetProperty("tone", out var toneEl) &&
            toneEl.ValueKind == JsonValueKind.String)
        {
            var t = toneEl.GetString();
            if (t == "incomplete" || t == "neutral" || t == "insufficient_data")
            {
                return (AnalysisSeverity.Unknown, null, SeverityHelpers.ExtractSummary(root));
            }
        }

        var severity = AnalysisSeverity.Unknown;

        if (root.TryGetProperty("summary", out var summary) &&
            summary.ValueKind == JsonValueKind.Object)
        {
            if (summary.TryGetProperty("signals_high", out var sh) && sh.GetInt32() > 0)
                severity = AnalysisSeverity.High;
            else if (summary.TryGetProperty("signals_medium", out var sm) && sm.GetInt32() > 0)
                severity = AnalysisSeverity.Moderate;
            else
                severity = AnalysisSeverity.Low;
        }

        if (severity == AnalysisSeverity.Unknown &&
            root.TryGetProperty("overall_tier", out var tier) &&
            tier.ValueKind == JsonValueKind.String)
        {
            severity = tier.GetString() switch
            {
                "very_low" or "low"   => AnalysisSeverity.Low,
                "moderate"            => AnalysisSeverity.Moderate,
                "high" or "very_high" => AnalysisSeverity.High,
                _                     => AnalysisSeverity.Unknown,
            };
        }

        severity = SeverityHelpers.InferFromTone(root, severity);
        severity = SeverityHelpers.InferFromStories(root, severity);

        severity = SeverityHelpers.ApplyToneOverride(root, severity);

        return (severity, null, SeverityHelpers.ExtractSummary(root));
    }
}
