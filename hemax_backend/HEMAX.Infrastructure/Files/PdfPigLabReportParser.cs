using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;
using HEMAX.Application.Common.Interfaces;
using Microsoft.Extensions.Logging;
using UglyToad.PdfPig;
using UglyToad.PdfPig.Content;

namespace HEMAX.Infrastructure.Files;

public class PdfPigLabReportParser : IPdfLabReportParser
{
    private readonly ILogger<PdfPigLabReportParser> _logger;


    private static readonly Dictionary<string, string[]> CbcPatterns = new()
    {
        ["wbc"] = new[] {
            @"(?<![A-Za-z])WBC(?![A-Za-z])", @"(?<!\p{L})Лейкоцит", @"(?<!\p{L})Leukocyt", @"(?<!\p{L})ЛЕЙКОЦИТ",
        },
        ["rbc"] = new[] {
            @"(?<![A-Za-z])RBC(?![A-Za-z])", @"(?<!\p{L})Еритроцит", @"(?<!\p{L})Эритроцит", @"(?<!\p{L})Erythrocyt",
        },
        ["hgb"] = new[] {
            @"(?<![A-Za-z])HGB(?![A-Za-z])", @"(?<![A-Za-z])HbG(?![A-Za-z])",
            @"(?<![A-Za-z])Hb(?![A-Za-z])",
            @"(?<!\p{L})Гемоглобін", @"(?<!\p{L})Гемоглобин", @"(?<!\p{L})Hemoglobin",
        },
        ["hct"] = new[] {
            @"(?<![A-Za-z])HCT(?![A-Za-z])", @"(?<!\p{L})Гематокрит", @"(?<!\p{L})Hematocrit",
        },
        ["plt"] = new[] {
            @"(?<![A-Za-z])PLT(?![A-Za-z])", @"(?<!\p{L})Тромбоцит", @"(?<!\p{L})Thrombocyt", @"(?<!\p{L})Platelet",
        },
        ["mcv"] = new[] {
            @"(?<![A-Za-z])MCV(?![A-Za-z])", @"Середній\s+об'?єм\s+еритроцита",
        },
        ["mch"] = new[] {
            @"(?<![A-Za-z])MCH(?![A-Za-z])",
            @"Середній\s+вміст\s+гемоглобіну",
        },
        ["mchc"] = new[] {
            @"(?<![A-Za-z])MCHC(?![A-Za-z])", @"Середня\s+концентрація\s+гемоглобіну",
        },
        ["rdw"] = new[] {
            @"(?<![A-Za-z])RDW(-CV|-SD)?(?![A-Za-z])", @"Розподіл\s+еритроцит",
        },
        ["mpv"] = new[] {
            @"(?<![A-Za-z])MPV(?![A-Za-z])", @"Середній\s+об'?єм\s+тромбоцита",
        },
        ["neu"] = new[] {
            @"(?<![A-Za-z])NEU(?![A-Za-z#])",
            @"(?<!\p{L})Нейтрофіл", @"(?<!\p{L})Нейтрофил", @"(?<!\p{L})Neutrophil",
        },
        ["lym"] = new[] {
            @"(?<![A-Za-z])LYM(?![A-Za-z#])",
            @"(?<!\p{L})Лімфоцит", @"(?<!\p{L})Лимфоцит", @"(?<!\p{L})Lymphocyt",
        },
        ["mon"] = new[] {
            @"(?<![A-Za-z])MON(?![A-Za-z#])", @"(?<![A-Za-z])MONO(?![A-Za-z#])",
            @"(?<!\p{L})Моноцит", @"(?<!\p{L})Monocyt",
        },
        ["eos"] = new[] {
            @"(?<![A-Za-z])EOS(?![A-Za-z#])",
            @"(?<!\p{L})Еозинофіл", @"(?<!\p{L})Эозинофил", @"(?<!\p{L})Eosinophil",
        },
        ["bas"] = new[] {
            @"(?<![A-Za-z])BAS(?![A-Za-z#])",
            @"(?<!\p{L})Базофіл", @"(?<!\p{L})Базофил", @"(?<!\p{L})Basophil",
        },
        ["anc"] = new[] {
            @"(?<![A-Za-z])ANC(?![A-Za-z])",
            @"(?<![A-Za-z])NEUT?#(?![A-Za-z])",
            @"Нейтрофіли[,\s]+абс", @"Нейтрофилы[,\s]+абс",
            @"Neutrophils[,\s]+abs",
        },
        ["alc"] = new[] {
            @"(?<![A-Za-z])ALC(?![A-Za-z])",
            @"(?<![A-Za-z])LYM#(?![A-Za-z])",
            @"Лімфоцити[,\s]+абс", @"Лимфоциты[,\s]+абс",
            @"Lymphocytes[,\s]+abs",
        },
        ["amc"] = new[] {
            @"(?<![A-Za-z])AMC(?![A-Za-z])",
            @"(?<![A-Za-z])MON#(?![A-Za-z])",
            @"Моноцити[,\s]+абс", @"Моноциты[,\s]+абс",
            @"Monocytes[,\s]+abs",
        },
        ["aec"] = new[] {
            @"(?<![A-Za-z])AEC(?![A-Za-z])",
            @"(?<![A-Za-z])EOS#(?![A-Za-z])",
            @"Еозинофіли[,\s]+абс", @"Эозинофилы[,\s]+абс",
            @"Eosinophils[,\s]+abs",
        },
        ["abc"] = new[] {
            @"(?<![A-Za-z])ABC(?![A-Za-z])",
            @"(?<![A-Za-z])BAS#(?![A-Za-z])",
            @"Базофіли[,\s]+абс", @"Базофилы[,\s]+абс",
            @"Basophils[,\s]+abs",
        },
        ["esr"] = new[] {
            @"(?<![A-Za-z])ESR(?![A-Za-z])",
            @"(?<!\p{L})ШОЕ(?!\p{L})", @"(?<!\p{L})СОЭ(?!\p{L})", @"(?<!\p{L})ШОЭ(?!\p{L})",
        },
    };

    private static readonly Dictionary<string, string[]> ChemPatterns = new()
    {
        ["glucose"] = new[] {
            @"Глюкоза", @"Глюкозы",
            @"(?<![A-Za-z])Glucose(?![A-Za-z])",
            @"(?<!\p{L})Глюк\.\s*кров",
            @"(?<![A-Za-z])GLU(?![A-Za-z])",
        },
        ["urea"] = new[] {
            @"(?<!\p{L})Urea(?!\p{L})", @"(?<!\p{L})Сечовина(?!\p{L})", @"(?<!\p{L})Мочевина(?!\p{L})",
        },
        ["creatinine"] = new[] {
            @"(?<!\p{L})Creatinine(?!\p{L})", @"(?<!\p{L})Креатинін(?!\p{L})", @"(?<!\p{L})Креатинин(?!\p{L})",
        },
        ["alt"] = new[] {
            @"(?<![A-Za-z])ALT(?![A-Za-z])", @"(?<!\p{L})АЛТ(?!\p{L})", @"(?<!\p{L})Алат(?!\p{L})",
        },
        ["ast"] = new[] {
            @"(?<![A-Za-z])AST(?![A-Za-z])", @"(?<!\p{L})АСТ(?!\p{L})", @"(?<!\p{L})Асат(?!\p{L})",
        },
        ["bilirubin_total"] = new[] {
            @"Білірубін\s+загальний", @"Билирубин\s+общий",
            @"Total\s+bilirubin", @"(?<![A-Za-z])TBIL(?![A-Za-z])",
        },
        ["bilirubin_direct"] = new[] {
            @"Білірубін\s+прямий", @"Билирубин\s+прямой",
            @"Direct\s+bilirubin", @"(?<![A-Za-z])DBIL(?![A-Za-z])",
        },
        ["cholesterol_total"] = new[] {
            @"Холестерин\s+загальний", @"Холестерин\s+общий",
            @"Total\s+cholesterol", @"(?<![A-Za-z])CHOL(?![A-Za-z])",
            @"(?<!\p{L})Холестерин", @"(?<!\p{L})Холестерол",
            @"(?<!\p{L})Cholesterol",
        },
        ["hdl"] = new[] {
            @"(?<![A-Za-z])HDL(?![A-Za-z])", @"(?<!\p{L})ХС-ЛПВЩ(?!\p{L})",
        },
        ["ldl"] = new[] {
            @"(?<![A-Za-z])LDL(?![A-Za-z])", @"(?<!\p{L})ХС-ЛПНЩ(?!\p{L})",
        },
        ["triglycerides"] = new[] {
            @"Тригліцериди", @"Триглицериды", @"(?<!\p{L})Triglycerides(?!\p{L})",
            @"(?<![A-Za-z])TG(?![A-Za-z])",
        },
        ["protein_total"] = new[] {
            @"Білок\s+загальний", @"Загальний\s+білок",
            @"Белок\s+общий", @"Total\s+protein",
        },
        ["albumin"] = new[] {
            @"(?<!\p{L})Albumin(?!\p{L})", @"(?<!\p{L})Альбумін(?!\p{L})", @"(?<!\p{L})Альбумин(?!\p{L})",
        },
        ["potassium"] = new[] {
            @"(?<!\p{L})Potassium(?!\p{L})", @"(?<!\p{L})Калій(?!\p{L})", @"(?<!\p{L})Калий(?!\p{L})",
            @"(?<![A-Za-z])K\+?(?![A-Za-z])",
        },
        ["sodium"] = new[] {
            @"(?<!\p{L})Sodium(?!\p{L})", @"(?<!\p{L})Натрій(?!\p{L})", @"(?<!\p{L})Натрий(?!\p{L})",
            @"(?<![A-Za-z])Na\+?(?![A-Za-z])",
        },
        ["calcium"] = new[] {
            @"(?<!\p{L})Calcium(?!\p{L})", @"(?<!\p{L})Кальцій(?!\p{L})", @"(?<!\p{L})Кальций(?!\p{L})",
            @"(?<![A-Za-z])Ca(?:[\u00B2\u207A2+]+)?(?![A-Za-z])",
        },

        ["a1c"] = new[] {
            @"(?<!\p{L})(?:HbA1c|Hb_A1c|A1C)(?!\p{L})", @"(?<!\p{L})Глікований\s+гемоглобін(?!\p{L})",
            @"(?<!\p{L})Гликированный\s+гемоглобин(?!\p{L})", @"(?<!\p{L})Глікозильований(?!\p{L})",
        },

        ["alp"] = new[] {
            @"(?<![A-Za-z])ALP(?![A-Za-z])",
            @"(?<!\p{L})Лужна\s+фосфатаза(?!\p{L})", @"(?<!\p{L})Щелочная\s+фосфатаза(?!\p{L})",
            @"(?<!\p{L})Alkaline\s+Phosphatase(?!\p{L})",
        },
        ["ggt"] = new[] {
            @"(?<![A-Za-z])GGT(?![A-Za-z])", @"(?<![A-Za-z])γ-?GT(?![A-Za-z])",
            @"(?<!\p{L})Гамма-?ГТ(?!\p{L})", @"(?<!\p{L})Гамма-?глутамілтрансфераза(?!\p{L})",
            @"(?<!\p{L})Gamma-?glutamyltransferase(?!\p{L})",
        },

        ["crp"] = new[] {
            @"(?<![A-Za-z])CRP(?![A-Za-z])", @"(?<![A-Za-z])hs-?CRP(?![A-Za-z])",
            @"(?<!\p{L})С-?реактивний\s+білок(?!\p{L})", @"(?<!\p{L})С-?реактивный\s+белок(?!\p{L})",
            @"(?<!\p{L})C-reactive\s+protein(?!\p{L})",
        },

        ["chloride"] = new[] {
            @"(?<!\p{L})Chloride(?!\p{L})", @"(?<!\p{L})Хлорид", @"(?<!\p{L})Хлор",
            @"(?<![A-Za-z])Cl-?(?![A-Za-z])",
        },
        ["bicarbonate"] = new[] {
            @"(?<!\p{L})Bicarbonate(?!\p{L})",
            @"(?<!\p{L})Бікарбонат", @"(?<!\p{L})Бикарбонат",
            @"(?<!\p{L})Гідрокарбонат", @"(?<!\p{L})Гидрокарбонат",
            @"(?<!\p{L})HCO3-?", @"(?<![A-Za-z])TCO2(?![A-Za-z])",
        },

        ["magnesium"] = new[] {
            @"(?<!\p{L})Magnesium(?!\p{L})", @"(?<!\p{L})Магній(?!\p{L})", @"(?<!\p{L})Магний(?!\p{L})",
            @"(?<![A-Za-z])Mg(?:[\u00B2\u207A2+]+)?(?![A-Za-z])",
        },
        ["phosphate"] = new[] {
            @"(?<!\p{L})Phosphate(?!\p{L})", @"(?<!\p{L})Phosphorus(?!\p{L})",
            @"(?<!\p{L})Фосфат(?!\p{L})", @"(?<!\p{L})Фосфор(?!\p{L})",
            @"(?<![A-Za-z])Phos(?![A-Za-z])",
        },

        ["iron"] = new[] {
            @"(?<!\p{L})Iron(?!\p{L})", @"(?<!\p{L})Залізо", @"(?<!\p{L})Железо",
            @"(?<![A-Za-z])Fe(?![A-Za-z])",
        },
        ["ferritin"] = new[] {
            @"(?<!\p{L})Ferritin(?!\p{L})", @"(?<!\p{L})Феритин(?!\p{L})", @"(?<!\p{L})Ферритин(?!\p{L})",
        },
        ["tibc"] = new[] {
            @"(?<![A-Za-z])TIBC(?![A-Za-z])", @"(?<!\p{L})ЗЗЗС(?!\p{L})",
            @"(?<!\p{L})Загальна\s+залізозв'язуюча\s+здатність(?!\p{L})",
            @"(?<!\p{L})Total\s+iron-?binding\s+capacity(?!\p{L})",
        },
        ["tsat"] = new[] {
            @"(?<![A-Za-z])TSAT(?![A-Za-z])",
            @"(?<!\p{L})Насичення\s+трансферину(?!\p{L})", @"(?<!\p{L})Насыщение\s+трансферрина(?!\p{L})",
            @"(?<!\p{L})Transferrin\s+saturation(?!\p{L})",
        },

        ["uric_acid"] = new[] {
            @"(?<!\p{L})Uric\s+acid(?!\p{L})", @"(?<!\p{L})Сечова\s+кислота(?!\p{L})", @"(?<!\p{L})Мочевая\s+кислота(?!\p{L})",
        },
        ["amylase"] = new[] {
            @"(?<!\p{L})Amylase(?!\p{L})", @"(?<!\p{L})α-?Amylase(?!\p{L})",
            @"(?<!\p{L})Амілаза(?!\p{L})", @"(?<!\p{L})Амилаза(?!\p{L})",
        },
        ["lipase"] = new[] {
            @"(?<!\p{L})Lipase(?!\p{L})", @"(?<!\p{L})Ліпаза(?!\p{L})", @"(?<!\p{L})Липаза(?!\p{L})",
        },
        ["ck"] = new[] {
            @"(?<![A-Za-z])CK(?![A-Za-z])", @"(?<![A-Za-z])CPK(?![A-Za-z])",
            @"(?<!\p{L})Креатинкіназа(?!\p{L})", @"(?<!\p{L})Креатинкиназа(?!\p{L})",
            @"(?<!\p{L})Creatine\s+kinase(?!\p{L})",
        },
        ["ldh"] = new[] {
            @"(?<![A-Za-z])LDH(?![A-Za-z])",
            @"(?<!\p{L})Лактатдегідрогеназа(?!\p{L})", @"(?<!\p{L})Лактатдегидрогеназа(?!\p{L})",
            @"(?<!\p{L})Lactate\s+dehydrogenase(?!\p{L})",
        },

        ["vitd_25oh"] = new[] {
            // CRITICAL ORDER: parenthesized "(25-OH)" notation first, so the
            // value scanner skips past the "(25-OH)" parens text and lands on
            // the actual number (e.g. "Вітамін D (25-OH) 42" → take 42, not 25).
            @"\(25-?OH\)", @"\(25-?\(OH\)\)",
            @"(?<!\p{L})25-?\(OH\)D", @"(?<!\p{L})25-?OH-?Vitamin\s*D",
            @"(?<!\p{L})25-?гідроксивітамін\s*D", @"(?<!\p{L})25-?гидроксивитамин\s*D",
            @"(?<!\p{L})Vitamin\s*D", @"(?<!\p{L})Вітамін\s*D", @"(?<!\p{L})Витамин\s*D",
        },
    };

    private static readonly Dictionary<string, string[]> LabBrands = new()
    {
        ["Synevo"]      = new[] { @"(?<!\p{L})Synevo(?!\p{L})", @"(?<!\p{L})Сіново(?!\p{L})" },
        ["Esculab"]     = new[] { @"(?<!\p{L})Esculab(?!\p{L})", @"(?<!\p{L})Ескулаб(?!\p{L})" },
        ["Diagnostika"] = new[] { @"(?<!\p{L})Diagnostika(?!\p{L})", @"(?<!\p{L})Діаgnostika(?!\p{L})" },
        ["Invitro"]     = new[] { @"(?<!\p{L})Invitro(?!\p{L})", @"(?<!\p{L})Інвітро(?!\p{L})", @"(?<!\p{L})Инвитро(?!\p{L})" },
        ["DILA"]        = new[] { @"(?<!\p{L})DILA(?!\p{L})", @"(?<!\p{L})Діла(?!\p{L})" },
    };

    public PdfPigLabReportParser(ILogger<PdfPigLabReportParser> logger)
    {
        _logger = logger;
    }

    public async Task<LabReportExtraction> ParseAsync(
        Stream pdfStream, string? hint, CancellationToken ct)
    {
        using var ms = new MemoryStream();
        await pdfStream.CopyToAsync(ms, ct);
        ms.Position = 0;

        var rawText = ExtractAllText(ms);
        if (string.IsNullOrWhiteSpace(rawText))
        {
            _logger.LogWarning("PDF has no extractable text — likely scanned/image PDF");
            return new LabReportExtraction(
                DetectedKind: hint ?? "unknown",
                Values: new Dictionary<string, double>(),
                Units: new Dictionary<string, string>(),
                LabName: null,
                Confidence: 0.0,
                RawText: ""
            );
        }

        var labName = DetectLab(rawText);
        var detectedKind = DetectKind(rawText, hint);

        var values = new Dictionary<string, double>();
        var units = new Dictionary<string, string>();

        var patterns = detectedKind switch
        {
            "cbc"  => CbcPatterns,
            "chem" => ChemPatterns,
            _ => CbcPatterns.Concat(ChemPatterns)
                  .ToDictionary(p => p.Key, p => p.Value),
        };

        foreach (var (code, namePatterns) in patterns)
        {
            foreach (var namePattern in namePatterns)
            {
                if (TryExtractValue(rawText, namePattern, out var value, out var unit))
                {
                    values[code] = value;
                    if (!string.IsNullOrEmpty(unit)) units[code] = unit;
                    break;  // first pattern that matches wins
                }
            }
        }

        double confidence;
        if (values.Count == 0)
        {
            confidence = 0.0;
        }
        else
        {
            var unitCoverage = values.Count == 0 ? 0.0
                : (double)units.Count / values.Count;
            confidence = Math.Min(1.0, 0.85 + 0.15 * unitCoverage);
        }

        var totalPatterns = patterns.Count;
        _logger.LogInformation(
            "PDF parse complete: kind={Kind}, lab={Lab}, matched={Matched}/{Total} "
            + "(panel coverage), with_units={WithUnits}/{Matched}, conf={Conf:F2}",
            detectedKind, labName, values.Count, totalPatterns,
            units.Count, values.Count, confidence);

        return new LabReportExtraction(
            DetectedKind: detectedKind,
            Values: values,
            Units: units,
            LabName: labName,
            Confidence: confidence,
            RawText: rawText.Length > 8000 ? rawText.Substring(0, 8000) : rawText
        );
    }


    private string ExtractAllText(Stream pdfStream)
    {
        var sb = new StringBuilder();
        using var document = PdfDocument.Open(pdfStream);
        foreach (var page in document.GetPages())
        {
            sb.AppendLine(page.Text);
        }
        return NormalizeRawText(sb.ToString());
    }

    private static string NormalizeRawText(string text)
    {
        if (string.IsNullOrEmpty(text)) return text;
        return Regex.Replace(
            text,
            @"(\d)(?=10(?:[\^][0-9]+|[\u00B2\u00B3\u00B9\u2070-\u2079]+)/)",
            "$1 ");
    }

    private static string? DetectLab(string text)
    {
        foreach (var (lab, patterns) in LabBrands)
        {
            foreach (var p in patterns)
            {
                if (Regex.IsMatch(text, p, RegexOptions.IgnoreCase))
                    return lab;
            }
        }
        return null;
    }

    private static string DetectKind(string text, string? hint)
    {
        if (!string.IsNullOrEmpty(hint)) return hint.ToLowerInvariant();

        var cbcHits = CbcPatterns.Count(kvp => kvp.Value.Any(p =>
            Regex.IsMatch(text, p, RegexOptions.IgnoreCase)));
        var chemHits = ChemPatterns.Count(kvp => kvp.Value.Any(p =>
            Regex.IsMatch(text, p, RegexOptions.IgnoreCase)));

        if (cbcHits >= chemHits && cbcHits >= 3) return "cbc";
        if (chemHits >= 3) return "chem";
        return "unknown";
    }

    private static bool TryExtractValue(
        string text, string namePattern, out double value, out string unit)
    {
        value = 0.0;
        unit = "";
        var match = Regex.Match(text, namePattern, RegexOptions.IgnoreCase);
        if (!match.Success) return false;

        var startIdx = match.Index + match.Length;
        if (startIdx >= text.Length) return false;

        var window = text.Substring(startIdx, Math.Min(80, text.Length - startIdx));

        var numMatch = Regex.Match(window,
            @"(?<num>[-+]?\d+(?:[.,]\d{1,3})?(?:[eE][-+]?\d+)?)\s*(?<unit>[a-zA-Zа-яА-Я%/×x⁹⁰¹²]{0,8})");
        if (!numMatch.Success) return false;

        var numStr = numMatch.Groups["num"].Value.Replace(',', '.');
        if (!double.TryParse(numStr, NumberStyles.Float, CultureInfo.InvariantCulture, out value))
            return false;

        unit = numMatch.Groups["unit"].Value.Trim().Trim('.', ',', ';', '-');
        return true;
    }
}
