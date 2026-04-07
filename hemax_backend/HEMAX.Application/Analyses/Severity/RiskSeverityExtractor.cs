using System.Text.Json;
using HEMAX.Domain.Enums;

namespace HEMAX.Application.Analyses.Severity;

public sealed class RiskSeverityExtractor : ISeverityExtractor
{
    public AnalysisType Type => AnalysisType.Risk;

    public (AnalysisSeverity severity, string? topFlag, string? summary) Extract(JsonElement root)
    {
        var severity = AnalysisSeverity.Unknown;

        if (root.TryGetProperty("overall_tier", out var tier) &&
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

        severity = SeverityHelpers.ApplyToneOverride(root, severity);
        return (severity, null, SeverityHelpers.ExtractSummary(root));
    }
}
