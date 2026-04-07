using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace HEMAX.Application.Analyses.Context;

internal static class ChemPayloadNormalizer
{
    private static readonly IReadOnlyDictionary<string, string> AnalyteUnits =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            // ── Glucose / diabetes ──
            ["glucose"]           = "mmol/L",
            ["a1c"]               = "%",            // Python parses "5.2%" or bare 5.2
            // ── Kidney ──
            ["creatinine"]        = "µmol/L",
            ["urea"]              = "mmol/L",
            ["bun"]               = "mmol/L",
            // ── Liver ──
            ["alt"]               = "U/L",
            ["ast"]               = "U/L",
            ["alp"]               = "U/L",
            ["ggt"]               = "U/L",
            ["bilirubin_total"]   = "µmol/L",
            ["bilirubin_direct"]  = "µmol/L",
            // ── Proteins ──
            ["albumin"]           = "g/L",
            ["total_protein"]     = "g/L",
            // ── Lipids ──
            ["cholesterol_total"] = "mmol/L",
            ["tchol"]             = "mmol/L",
            ["hdl"]               = "mmol/L",
            ["ldl"]               = "mmol/L",
            ["triglycerides"]     = "mmol/L",
            ["trigly"]            = "mmol/L",
            // ── Inflammation ──
            ["crp"]               = "mg/L",
            // ── Electrolytes ──
            ["sodium"]            = "mmol/L",
            ["potassium"]         = "mmol/L",
            ["chloride"]          = "mmol/L",
            ["bicarbonate"]       = "mmol/L",
            // ── Minerals ──
            ["calcium"]           = "mmol/L",
            ["magnesium"]         = "mmol/L",
            ["phosphate"]         = "mmol/L",
            ["phosphorus"]        = "mmol/L",
            // ── Iron panel ──
            ["iron"]              = "µmol/L",
            ["ferritin"]          = "ng/mL",
            ["tibc"]              = "µmol/L",
            ["tsat"]              = "%",
            // ── Other ──
            ["uric_acid"]         = "µmol/L",
            ["amylase"]           = "U/L",
            ["lipase"]            = "U/L",
            ["ck"]                = "U/L",
            ["ldh"]               = "U/L",
            ["vitd_25oh"]         = "ng/mL",
        };

    private static readonly HashSet<string> ContextKeys = new(StringComparer.OrdinalIgnoreCase)
    {
        "sex", "age", "labs", "fasting_hours", "fasting_8h", "ref_ranges", "context",
    };

    public static string Normalize(string payloadJson)
    {
        if (string.IsNullOrWhiteSpace(payloadJson)) return payloadJson;

        JsonNode? root;
        try
        {
            root = JsonNode.Parse(payloadJson);
        }
        catch (JsonException)
        {
            return payloadJson;
        }
        if (root is not JsonObject obj) return payloadJson;

        AttachUnitsInPlace(obj);
        if (obj["labs"] is JsonObject labs) AttachUnitsInPlace(labs);

        return root.ToJsonString();
    }

    private static void AttachUnitsInPlace(JsonObject obj)
    {
        foreach (var key in obj.Select(kv => kv.Key).ToList())
        {
            if (ContextKeys.Contains(key)) continue;
            if (!AnalyteUnits.TryGetValue(key, out var unit)) continue;
            if (obj[key] is not JsonValue val) continue;

            if (val.TryGetValue<string>(out _)) continue;
            if (!val.TryGetValue<double>(out var n)) continue;

            obj[key] = JsonValue.Create(
                n.ToString(CultureInfo.InvariantCulture) + " " + unit);
        }
    }
}
