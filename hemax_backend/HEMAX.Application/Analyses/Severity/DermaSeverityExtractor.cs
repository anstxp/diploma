using System.Text.Json;
using HEMAX.Domain.Enums;

namespace HEMAX.Application.Analyses.Severity;

public sealed class DermaSeverityExtractor : ISeverityExtractor
{
    public AnalysisType Type => AnalysisType.Derma;

    public (AnalysisSeverity severity, string? topFlag, string? summary) Extract(JsonElement root)
    {
        var severity = AnalysisSeverity.Unknown;
        string? topFlag = null;

        if (root.TryGetProperty("severity", out var sev) &&
            sev.ValueKind == JsonValueKind.String)
        {
            severity = sev.GetString() switch
            {
                "low"      => AnalysisSeverity.Low,
                "medium"   => AnalysisSeverity.Moderate,
                "high"     => AnalysisSeverity.High,
                "critical" => AnalysisSeverity.Critical,
                _          => AnalysisSeverity.Unknown,
            };
        }

        if (root.TryGetProperty("top_class", out var tc) &&
            tc.ValueKind == JsonValueKind.String)
        {
            topFlag = tc.GetString();
        }

        severity = SeverityHelpers.ApplyToneOverride(root, severity);
        return (severity, topFlag, SeverityHelpers.ExtractSummary(root));
    }
}
