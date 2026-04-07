using System.Text.Json;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Enums;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Analyses.Context;

public interface IRecentLabsMerger
{
    Task<string> MergeAsync(string payloadJson, Guid userId, CancellationToken ct);
}

internal sealed class RecentLabsMerger : IRecentLabsMerger
{
    private readonly IHemaxDbContext _db;

    private static readonly HashSet<string> NonLabKeys = new(StringComparer.OrdinalIgnoreCase)
    {
        "sex", "age", "labs", "fasting_hours", "fasting_8h",
    };

    public RecentLabsMerger(IHemaxDbContext db) { _db = db; }

    public async Task<string> MergeAsync(
        string payloadJson, Guid userId, CancellationToken ct)
    {
        var recentCbc = await LoadMostRecent(userId, AnalysisType.Cbc, ct);
        var recentChem = await LoadMostRecent(userId, AnalysisType.Chem, ct);

        if (recentCbc is null && recentChem is null) return payloadJson;

        var payloadNode = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(payloadJson)
                          ?? new Dictionary<string, JsonElement>();

        var labs = new Dictionary<string, object?>();
        AbsorbCbcOrChem(recentCbc, labs);
        AbsorbCbcOrChem(recentChem, labs);

        if (payloadNode.TryGetValue("labs", out var currentLabs) &&
            currentLabs.ValueKind == JsonValueKind.Object)
        {
            foreach (var prop in currentLabs.EnumerateObject())
                labs[prop.Name] = ToObject(prop.Value);
        }

        // ──────────────────────────────────────────────────────────────────
        // Bug fix May 2026: unit-string normalisation. CHEM values stored
        // in RawInputJson look like "5.4 mmol/L" because ChemPayloadNormalizer
        // wraps them on the way INTO the CHEM service. When we pull them
        // back out and feed them to RISK or NEURO, those services historically
        // did `float("5.4 mmol/L")` which throws and silently drops the
        // feature. After this patch each value is run through
        // LabUnitConverter, which:
        //   - leaves numeric values unchanged (CBC stores raw numbers)
        //   - parses unit-tagged strings and converts to the canonical
        //     numeric unit (mmol/L glucose → mg/dL, µmol/L creatinine → mg/dL,
        //     etc. — see LabUnitConverter for the per-analyte factors).
        // This makes the merger correct independent of whether the Python
        // RISK/NEURO services have units.py shimmed in or not. Defense in
        // depth: both sides handle the issue.
        // ──────────────────────────────────────────────────────────────────
        var normalized = new Dictionary<string, object?>(labs.Count);
        foreach (var (key, value) in labs)
        {
            normalized[key] = LabUnitConverter.Convert(key, value);
        }

        payloadNode["labs"] = JsonSerializer.SerializeToElement(normalized);
        return JsonSerializer.Serialize(payloadNode);
    }

    private async Task<string?> LoadMostRecent(Guid userId, AnalysisType type, CancellationToken ct) =>
        await _db.Analyses
            .Where(a => a.UserId == userId && a.Type == type)
            .OrderByDescending(a => a.CreatedAt)
            .Select(a => a.RawInputJson)
            .FirstOrDefaultAsync(ct);

    private static void AbsorbCbcOrChem(string? json, Dictionary<string, object?> labs)
    {
        if (string.IsNullOrWhiteSpace(json)) return;
        try
        {
            using var doc = JsonDocument.Parse(json);
            foreach (var prop in doc.RootElement.EnumerateObject())
            {
                if (NonLabKeys.Contains(prop.Name)) continue;
                if (prop.Value.ValueKind is JsonValueKind.Number or JsonValueKind.String)
                    labs[prop.Name] = ToObject(prop.Value);
            }
            // CHEM has a nested "labs" object.
            if (doc.RootElement.TryGetProperty("labs", out var nested) &&
                nested.ValueKind == JsonValueKind.Object)
            {
                foreach (var prop in nested.EnumerateObject())
                {
                    if (prop.Value.ValueKind is JsonValueKind.Number or JsonValueKind.String)
                        labs[prop.Name] = ToObject(prop.Value);
                }
            }
        }
        catch (JsonException) { /* skip malformed historical payload */ }
    }

    private static object? ToObject(JsonElement v) => v.ValueKind switch
    {
        JsonValueKind.Number => v.GetDouble(),
        JsonValueKind.String => v.GetString(),
        _                    => null,
    };
}
