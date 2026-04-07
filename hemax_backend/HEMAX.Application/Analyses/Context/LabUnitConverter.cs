using System.Globalization;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace HEMAX.Application.Analyses.Context;

internal static class LabUnitConverter
{
    public static string NormalizePayloadLabs(string payloadJson)
    {
        if (string.IsNullOrWhiteSpace(payloadJson)) return payloadJson;

        Dictionary<string, JsonElement>? node;
        try
        {
            node = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(payloadJson);
        }
        catch (JsonException)
        {
            return payloadJson;  // malformed — let downstream complain
        }
        if (node is null) return payloadJson;

        if (!node.TryGetValue("labs", out var labsEl) ||
            labsEl.ValueKind != JsonValueKind.Object)
        {
            return payloadJson;
        }

        var normalized = new Dictionary<string, object?>();
        foreach (var prop in labsEl.EnumerateObject())
        {
            object? boxedValue = prop.Value.ValueKind switch
            {
                JsonValueKind.Number => prop.Value.GetDouble(),
                JsonValueKind.String => prop.Value.GetString(),
                _                    => null,
            };
            normalized[prop.Name] = Convert(prop.Name, boxedValue);
        }

        node["labs"] = JsonSerializer.SerializeToElement(normalized);
        return JsonSerializer.Serialize(node);
    }

    public static object? Convert(string analyteName, object? value)
    {
        if (value is null) return null;

        // Numeric values: assume already canonical, no conversion.
        // (If a caller is sending raw numbers in mmol/L without going
        // through ChemPayloadNormalizer first, that's a separate bug
        // and not this helper's job.)
        if (value is double || value is int || value is float || value is decimal)
            return value;

        if (value is not string s || string.IsNullOrWhiteSpace(s))
            return value;

        var (number, unit) = ParseValueAndUnit(s);
        if (number is null) return value;        // unparseable — pass through
        if (unit is null)   return number.Value; // bare number string → numeric

        var key = analyteName.ToLowerInvariant();
        var u   = unit.ToLowerInvariant();

        if (IsGlucoseLike(key))
        {
            return u switch
            {
                "mmol/l"        => number.Value * 18.018,
                "mg/dl"         => number.Value,
                _               => number.Value,    // unknown → assume canonical
            };
        }

        if (IsCholesterolLike(key))
        {
            return u switch
            {
                "mmol/l" => number.Value * 38.67,
                "mg/dl"  => number.Value,
                _        => number.Value,
            };
        }

        // Triglycerides: mmol/L → mg/dL (×88.57)
        if (key.Contains("triglycer") || key.Contains("тригліцерид"))
        {
            return u switch
            {
                "mmol/l" => number.Value * 88.57,
                "mg/dl"  => number.Value,
                _        => number.Value,
            };
        }

        if (key.Contains("creatinine") || key.Contains("креатинін"))
        {
            return u switch
            {
                "µmol/l" or "umol/l" or "мкмоль/л" => number.Value / 88.4,
                "mg/dl"                             => number.Value,
                _                                   => number.Value,
            };
        }

        if (key.Contains("urea") || key.Contains("сечовина") ||
            key.Contains("bun"))
        {
            return u switch
            {
                "mmol/l" => number.Value * 2.801,
                "mg/dl"  => number.Value,
                _        => number.Value,
            };
        }

        // Uric acid: µmol/L → mg/dL (÷59.48)
        if (key.Contains("uric") || key.Contains("urate") || key.Contains("сечова"))
        {
            return u switch
            {
                "µmol/l" or "umol/l" or "мкмоль/л" => number.Value / 59.48,
                "mg/dl"                             => number.Value,
                _                                   => number.Value,
            };
        }

        // Bilirubin: µmol/L → mg/dL (÷17.1)
        if (key.Contains("bilirubin") || key.Contains("білірубін"))
        {
            return u switch
            {
                "µmol/l" or "umol/l" or "мкмоль/л" => number.Value / 17.1,
                "mg/dl"                             => number.Value,
                _                                   => number.Value,
            };
        }

        if (key.Contains("hba1c") || key.Contains("a1c") || key.Contains("глікован"))
        {
            return number.Value;
        }

        return number.Value;
    }


    private static bool IsGlucoseLike(string key) =>
        key.Contains("glucose") || key.Contains("глюкоз") || key == "glu";

    private static bool IsCholesterolLike(string key) =>
        key.Contains("cholesterol") || key.Contains("холестерин") ||
        key == "tchol" || key == "ldl" || key == "hdl" || key == "non_hdl";

    private static readonly Regex NumberUnitRx = new(
        @"^\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*([a-zA-Zµμмкгмольдлл\u0400-\u04FF/%]+)?\s*$",
        RegexOptions.Compiled);

    private static (double? number, string? unit) ParseValueAndUnit(string s)
    {
        var m = NumberUnitRx.Match(s);
        if (!m.Success) return (null, null);

        if (!double.TryParse(m.Groups[1].Value, NumberStyles.Float,
                              CultureInfo.InvariantCulture, out var num))
            return (null, null);

        var unit = m.Groups[2].Success ? m.Groups[2].Value : null;
        if (unit is not null)
        {
            unit = unit.Replace('μ', 'µ');  // GREEK SMALL LETTER MU → MICRO SIGN
        }
        return (num, unit);
    }
}
