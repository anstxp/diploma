using System.Text.Json;
using HEMAX.Domain.Enums;
using Microsoft.Extensions.Logging;

namespace HEMAX.Application.Analyses.Severity;

public interface ISeverityExtractorRegistry
{
    (AnalysisSeverity severity, string? topFlag, string? summary)
        Extract(string json, AnalysisType type);
}

internal sealed class SeverityExtractorRegistry : ISeverityExtractorRegistry
{
    private readonly Dictionary<AnalysisType, ISeverityExtractor> _byType;
    private readonly ILogger<SeverityExtractorRegistry> _logger;

    public SeverityExtractorRegistry(
        IEnumerable<ISeverityExtractor> extractors,
        ILogger<SeverityExtractorRegistry> logger)
    {
        _byType = extractors.ToDictionary(e => e.Type);
        _logger = logger;
    }

    public (AnalysisSeverity severity, string? topFlag, string? summary)
        Extract(string json, AnalysisType type)
    {
        if (!_byType.TryGetValue(type, out var extractor))
        {
            _logger.LogWarning("No severity extractor registered for {Type}", type);
            return (AnalysisSeverity.Unknown, null, null);
        }

        try
        {
            using var doc = JsonDocument.Parse(json);
            return extractor.Extract(doc.RootElement);
        }
        catch (JsonException ex)
        {
            _logger.LogWarning(ex,
                "Failed to parse {Type} response for severity extraction.", type);
            return (AnalysisSeverity.Unknown, null, null);
        }
    }
}
