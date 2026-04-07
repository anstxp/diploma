using System.Text.Json;
using HEMAX.Domain.Enums;

namespace HEMAX.Application.Analyses.Severity;

public interface ISeverityExtractor
{
    AnalysisType Type { get; }

    (AnalysisSeverity severity, string? topFlag, string? summary) Extract(JsonElement root);
}
