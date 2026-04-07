using System.Text.Json;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Analyses.Context;

public interface IPatientContextBuilder
{
    Task<string> InjectContextAsync(string payloadJson, Guid userId, CancellationToken ct);
}

internal sealed class PatientContextBuilder : IPatientContextBuilder
{
    private readonly IHemaxDbContext _db;

    public PatientContextBuilder(IHemaxDbContext db) { _db = db; }

    public async Task<string> InjectContextAsync(
        string payloadJson, Guid userId, CancellationToken ct)
    {
        var profile = await _db.UserProfiles
            .FirstOrDefaultAsync(p => p.UserId == userId, ct);
        if (profile is null) return payloadJson;

        var profileFlags = BuildFlags(profile);
        if (profileFlags.Count == 0) return payloadJson;

        var node = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(payloadJson)
                   ?? new Dictionary<string, JsonElement>();

        // ──────────────────────────────────────────────────────────────────
        // Bug fix May 2026: MERGE form context with profile context instead
        // of overwriting. Previously line was:
        //     node["context"] = JsonSerializer.SerializeToElement(profileFlags);
        // which silently destroyed user checkbox input from RiskForm/NeuroForm
        // (smoker, sedentary, alcohol_regular, etc.) the moment the profile
        // contributed any flag at all — even an unrelated one like
        // "family_diabetes". Now we read whatever the frontend already
        // attached, merge with profile-derived flags via OR semantics
        // (true wins), and write back the merged dict.
        //
        // OR semantics, not "form wins" or "profile wins", because:
        //   - If the user ticks "smoker" in the form, that beats an outdated
        //     profile saying "non-smoker" (form is the fresh signal).
        //   - If the profile says has_diabetes=true and the form has nothing
        //     about diabetes, we still want has_diabetes=true to reach the
        //     ML model.
        //   - There's no case where a true flag should be erased by a
        //     missing/false flag from the other source.
        // ──────────────────────────────────────────────────────────────────
        var merged = new Dictionary<string, bool>(profileFlags);

        if (node.TryGetValue("context", out var existingCtx) &&
            existingCtx.ValueKind == JsonValueKind.Object)
        {
            foreach (var prop in existingCtx.EnumerateObject())
            {
                bool? formValue = prop.Value.ValueKind switch
                {
                    JsonValueKind.True  => true,
                    JsonValueKind.False => false,
                    JsonValueKind.String when prop.Value.GetString()?.ToLowerInvariant() == "true"  => true,
                    JsonValueKind.String when prop.Value.GetString()?.ToLowerInvariant() == "false" => false,
                    _ => null,
                };
                if (formValue is null)
                {
                    continue;
                }

                // OR-merge: any true wins.
                merged[prop.Name] = merged.GetValueOrDefault(prop.Name) || formValue.Value;
            }
        }

        using var doc = JsonDocument.Parse(
            JsonSerializer.Serialize(merged));
        var mergedNode = doc.RootElement.Deserialize<Dictionary<string, JsonElement>>()
                         ?? new Dictionary<string, JsonElement>();

        if (node.TryGetValue("context", out var origCtx) &&
            origCtx.ValueKind == JsonValueKind.Object)
        {
            foreach (var prop in origCtx.EnumerateObject())
            {
                if (prop.Value.ValueKind is not JsonValueKind.True
                                         and not JsonValueKind.False)
                {
                    mergedNode[prop.Name] = prop.Value.Clone();
                }
            }
        }

        node["context"] = JsonSerializer.SerializeToElement(mergedNode);
        return JsonSerializer.Serialize(node);
    }

    private static readonly Dictionary<string, string[]> ConditionKeywords = new()
    {
        ["has_diabetes"]       = new[] { "діабет", "diabetes", "цд", "т2цд", "т1цд", "гіперглікем" },
        ["has_hypertension"]   = new[] { "гіпертенз", "гіпертоні", "hypertension", "підвищений тиск", "артеріальн" },
        ["has_kidney_disease"] = new[] { "ниркова", "ххн", "ckd", "нефропат", "пієлонефрит", "діаліз" },
        ["has_liver_disease"]  = new[] { "гепатит", "цироз", "стеатоз", "печінкова", "nafld", "насг" },
        ["has_thyroid"]        = new[] { "щитовидн", "тиреоїди", "гіпотиреоз", "гіпертиреоз", "хашимото", "грейвса" },
        ["has_cardiac"]        = new[] { "іхс", "інфаркт", "стенокарді", "аритмі", "серцева недостат", "фібриляц" },
        ["has_anemia_history"] = new[] { "анемі", "anemia", "залізодефіцит", "b12-дефіцит" },
        ["has_autoimmune"]     = new[] { "вовчак", "артрит", "ревматоїд", "склероз", "псоріаз", "крон", "целіакі" },
        ["has_cancer_history"] = new[] { "онколог", "хіміо", "промене", "пухлин", "карцином", "лімфом", "лейкемі" },
        ["is_pregnant"]        = new[] { "вагітн", "pregnan" },
        ["recent_surgery"]     = new[] { "операці", "хірургічн", "після операці" },
    };

    private static readonly Dictionary<string, string[]> MedicationKeywords = new()
    {
        ["takes_statins"]         = new[] { "статин", "розувастатин", "аторвастатин", "сімвастатин", "правастатин", "lipitor", "crestor" },
        ["takes_metformin"]       = new[] { "метформін", "metformin", "сіофор", "глюкофаж" },
        ["takes_insulin"]         = new[] { "інсулін", "insulin", "лантус", "хумалог", "новорапід", "тресіба", "лізпро", "детемір" },
        ["takes_anticoagulants"]  = new[] { "варфарин", "warfarin", "ривароксабан", "апіксабан", "дабігатран", "клопідогрель", "ксарелто", "елікіс", "прадакса", "аспірин", "аспекард" },
        ["takes_corticosteroids"] = new[] { "преднізолон", "дексаметазон", "метилпреднізолон", "кортикостероїд", "стероїд", "медрол", "солу-медрол" },
        ["takes_diuretics"]       = new[] { "фуросемід", "торасемід", "індапамід", "діуретик", "гіпотіазид", "гідрохлортіазид", "спіронолактон", "верошпірон", "трифас", "лазикс" },
        ["takes_beta_blockers"]   = new[] { "бісопролол", "метопролол", "карведилол", "небіволол", "бета-блокатор", "конкор", "коріол" },
        ["takes_ace_inhibitors"]  = new[] {
            "еналаприл", "лізиноприл", "періндоприл", "інгібітор апф", "раміприл", "каптоприл", "берліприл",
            // ARBs
            "лозартан", "валсартан", "телмісартан", "ірбесартан", "кандесартан", "олмесартан",
            "лозап", "діован", "мікардіс", "апровель", "апф/арб", "арб", "сартан"
        },
        ["takes_chemotherapy"]    = new[] { "хіміотерапі", "циклофосфамід", "доксорубіцин", "метотрексат", "цисплатин" },
        ["takes_thyroid_meds"]    = new[] { "l-тироксин", "еутирокс", "тироксин", "тиреостат", "мерказоліл", "тирозол" },
        ["takes_oral_diabetics_other"] = new[] {
            "емпагліфлозин", "дапагліфлозин", "канагліфлозин", "ертугліфлозин",  // SGLT2
            "ситагліптин", "вілдагліптин", "лінагліптин", "саксагліптин",        // DPP4
            "глімепірид", "гліклазид", "глібенкламід",                            // sulfonylureas
            "піоглітазон", "розиглітазон",                                        // TZDs
            "форсіга", "джардінс", "галвус", "янувія", "діабетон", "амарил"      // brand names
        },
    };

    private static readonly Dictionary<string, string[]> FamilyKeywords = new()
    {
        ["family_diabetes"] = new[] { "діабет" },
        ["family_cvd"]      = new[] { "інфаркт", "інсульт", "ссз", "коронар" },
        ["family_cancer"]   = new[] { "рак", "онколог", "пухлин" },
    };

    private static Dictionary<string, bool> BuildFlags(UserProfile profile)
    {
        var flags = new Dictionary<string, bool>();
        ApplyKeywords(flags, profile.ChronicDiseases, ConditionKeywords);
        ApplyKeywords(flags, profile.CurrentMedications, MedicationKeywords);
        ApplyKeywords(flags, profile.FamilyHistory, FamilyKeywords);

        if (profile.Smoker) flags["smoker"] = true;
        if (profile.AlcoholFrequency == AlcoholFrequency.Regular ||
            profile.AlcoholFrequency == AlcoholFrequency.Heavy)
            flags["alcohol_regular"] = true;
        if (profile.PhysicalActivity == PhysicalActivity.Sedentary)
            flags["sedentary"] = true;

        AddAliases(flags);

        return flags;
    }

    private static void AddAliases(Dictionary<string, bool> flags)
    {
        // Conditions
        Mirror(flags, "has_kidney_disease",  "has_ckd");
        Mirror(flags, "has_cardiac",         "has_cardiovascular_disease");
        Mirror(flags, "is_pregnant",         "pregnant");

        Mirror(flags, "takes_statins",         "on_statins");
        Mirror(flags, "takes_anticoagulants",  "on_oral_anticoagulants");
        Mirror(flags, "takes_corticosteroids", "on_corticosteroids");
        Mirror(flags, "takes_diuretics",       "on_diuretics");
        Mirror(flags, "takes_ace_inhibitors",  "on_acei_arb");
        Mirror(flags, "takes_insulin",         "on_insulin");

        if (flags.GetValueOrDefault("takes_metformin") ||
            flags.GetValueOrDefault("takes_oral_diabetics_other"))
            flags["on_oral_diabetics"] = true;
    }

    private static void Mirror(Dictionary<string, bool> flags, string src, string dst)
    {
        if (flags.GetValueOrDefault(src)) flags[dst] = true;
        if (flags.GetValueOrDefault(dst)) flags[src] = true;
    }

    private static void ApplyKeywords(
        Dictionary<string, bool> flags, string? text,
        Dictionary<string, string[]> dict)
    {
        if (string.IsNullOrWhiteSpace(text)) return;
        var lower = text.ToLowerInvariant();
        foreach (var (flagName, keywords) in dict)
        {
            if (keywords.Any(kw => lower.Contains(kw, StringComparison.OrdinalIgnoreCase)))
                flags[flagName] = true;
        }
    }
}
