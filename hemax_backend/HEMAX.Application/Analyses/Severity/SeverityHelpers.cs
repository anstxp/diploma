using System.Text.Json;
using HEMAX.Domain.Enums;

namespace HEMAX.Application.Analyses.Severity;

internal static class SeverityHelpers
{
    public const int MaxSummaryLength = 500;

    public static string? ExtractSummary(JsonElement root)
    {
        if (root.TryGetProperty("summary", out var summary))
        {
            if (summary.ValueKind == JsonValueKind.String)
                return Cap(summary.GetString());
            if (summary.ValueKind == JsonValueKind.Object &&
                summary.TryGetProperty("headline", out var headline))
                return Cap(headline.GetString());
        }
        if (root.TryGetProperty("headline", out var topHeadline) &&
            topHeadline.ValueKind == JsonValueKind.String)
            return Cap(topHeadline.GetString());
        return null;
    }

    private static string? Cap(string? s) =>
        string.IsNullOrEmpty(s) || s.Length <= MaxSummaryLength
            ? s : s.Substring(0, MaxSummaryLength);

    /// <summary>
    /// "tone": "urgent" elevates any severity to Critical. Used by Risk
    /// and Neuro services as a way to short-circuit the tier mapping when
    /// the model is highly confident something is wrong.
    /// </summary>
    public static AnalysisSeverity ApplyToneOverride(JsonElement root, AnalysisSeverity current)
    {
        if (root.TryGetProperty("tone", out var tone) &&
            tone.ValueKind == JsonValueKind.String &&
            tone.GetString() == "urgent")
        {
            return AnalysisSeverity.Critical;
        }
        return current;
    }

    public static AnalysisSeverity InferFromTone(JsonElement root, AnalysisSeverity current)
    {
        if (current != AnalysisSeverity.Unknown) return current;
        if (!root.TryGetProperty("tone", out var tone) ||
            tone.ValueKind != JsonValueKind.String) return current;

        return tone.GetString() switch
        {
            "urgent"                                       => AnalysisSeverity.Critical,
            "attention_needed" or "elevated" or "warning"  => AnalysisSeverity.Moderate,
            "normal" or "calm" or "reassuring" or "ok"     => AnalysisSeverity.Low,
            _                                              => current,
        };
    }

    /// <summary>
    /// Final narrative-shape fallback: scan <c>stories[]</c> and return
    /// the max per-story severity. CHEM/CBC narrative engines emit
    /// per-story <c>severity</c> fields ("low" / "moderate" / "high" /
    /// "critical"). If stories exist but none carry a usable severity,
    /// surface Moderate so the UI shows "there's something here" rather
    /// than a confusing "Unknown" next to visible findings.
    ///
    /// Only runs when current severity is still Unknown.
    /// </summary>
    public static AnalysisSeverity InferFromStories(JsonElement root, AnalysisSeverity current)
    {
        if (current != AnalysisSeverity.Unknown) return current;
        if (!root.TryGetProperty("stories", out var stories) ||
            stories.ValueKind != JsonValueKind.Array) return current;

        var max = AnalysisSeverity.Unknown;
        var hasAny = false;

        foreach (var story in stories.EnumerateArray())
        {
            hasAny = true;
            if (!story.TryGetProperty("severity", out var ss) ||
                ss.ValueKind != JsonValueKind.String) continue;

            var mapped = ss.GetString() switch
            {
                "critical" or "urgent" or "very_high" => AnalysisSeverity.Critical,
                "high"                                => AnalysisSeverity.High,
                "moderate" or "medium" or "elevated"  => AnalysisSeverity.Moderate,
                "low" or "very_low" or "calm"         => AnalysisSeverity.Low,
                _                                     => AnalysisSeverity.Unknown,
            };
            if ((int)mapped > (int)max) max = mapped;
        }

        if (hasAny && max == AnalysisSeverity.Unknown)
            return AnalysisSeverity.Moderate;

        return max;
    }
}
