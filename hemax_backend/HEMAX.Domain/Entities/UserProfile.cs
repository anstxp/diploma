using HEMAX.Domain.Common;
using HEMAX.Domain.Enums;

namespace HEMAX.Domain.Entities;

public class UserProfile
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid UserId { get; set; }
    public ApplicationUser User { get; set; } = null!;

    [Encrypted] public string? MiddleName { get; set; }
    [Encrypted] public string? Phone { get; set; }

    public string? PhoneHash { get; set; }

    public double? HeightCm { get; set; }
    public double? WeightKg { get; set; }
    public double? WaistCm { get; set; }

    public double? TypicalSystolicBp  { get; set; }
    public double? TypicalDiastolicBp { get; set; }
    public double? TypicalRestingPulse { get; set; }

    [Encrypted] public string? ChronicDiseases { get; set; }
    [Encrypted] public string? Allergies { get; set; }
    [Encrypted] public string? CurrentMedications { get; set; }
    [Encrypted] public string? FamilyHistory { get; set; }

    public bool Smoker { get; set; }
    public AlcoholFrequency AlcoholFrequency { get; set; } = AlcoholFrequency.Unknown;
    public PhysicalActivity PhysicalActivity { get; set; } = PhysicalActivity.Unknown;
    public DietType DietType { get; set; } = DietType.Unknown;

    [Encrypted] public string? EmergencyContactName { get; set; }
    [Encrypted] public string? EmergencyContactPhone { get; set; }
    public string? EmergencyContactRelation { get; set; }

    public string PreferredLanguage { get; set; } = "uk";
    public string UnitsSystem { get; set; } = "metric";

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset UpdatedAt { get; set; } = DateTimeOffset.UtcNow;

    public double? Bmi
    {
        get
        {
            if (HeightCm is null or <= 0 || WeightKg is null or <= 0) return null;
            var hM = HeightCm.Value / 100.0;
            return Math.Round(WeightKg.Value / (hM * hM), 1);
        }
    }
}
