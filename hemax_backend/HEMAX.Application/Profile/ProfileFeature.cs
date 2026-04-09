using FluentValidation;
using HEMAX.Domain.Enums;
using MediatR;

namespace HEMAX.Application.UserProfiles;

public record UserProfileDto(
    // From ApplicationUser
    Guid   UserId,
    string Email,
    string FirstName,
    string LastName,
    string? MiddleName,
    DateOnly? DateOfBirth,
    int?   Age,
    Sex    Sex,
    string? AvatarUrl,
    string? Phone,

    // Anthropometrics
    double? HeightCm,
    double? WeightKg,
    double? WaistCm,
    double? Bmi,

    // Vitals
    double? TypicalSystolicBp,
    double? TypicalDiastolicBp,
    double? TypicalRestingPulse,

    // Medical history
    string? ChronicDiseases,
    string? Allergies,
    string? CurrentMedications,
    string? FamilyHistory,

    // Lifestyle
    bool   Smoker,
    AlcoholFrequency AlcoholFrequency,
    PhysicalActivity PhysicalActivity,
    DietType DietType,

    // Emergency contact
    string? EmergencyContactName,
    string? EmergencyContactPhone,
    string? EmergencyContactRelation,

    // Settings
    string PreferredLanguage,
    string UnitsSystem
);

public record UpdateProfileRequest(
    string? FirstName,
    string? LastName,
    string? MiddleName,
    DateOnly? DateOfBirth,
    Sex? Sex,
    string? Phone,

    double? HeightCm,
    double? WeightKg,
    double? WaistCm,

    double? TypicalSystolicBp,
    double? TypicalDiastolicBp,
    double? TypicalRestingPulse,

    string? ChronicDiseases,
    string? Allergies,
    string? CurrentMedications,
    string? FamilyHistory,

    bool? Smoker,
    AlcoholFrequency? AlcoholFrequency,
    PhysicalActivity? PhysicalActivity,
    DietType? DietType,

    string? EmergencyContactName,
    string? EmergencyContactPhone,
    string? EmergencyContactRelation,

    string? PreferredLanguage,
    string? UnitsSystem
);


public record GetMyProfileQuery() : IRequest<UserProfileDto>;
public record GetUserProfileQuery(Guid UserId) : IRequest<UserProfileDto>;
public record UpdateMyProfileCommand(UpdateProfileRequest Body) : IRequest<UserProfileDto>;


public class UpdateProfileValidator : AbstractValidator<UpdateProfileRequest>
{
    private const string NameRegex = @"^[\p{L}\p{M}\s'\u2019\-]+$";
    private const int MinAge = 13;

    public UpdateProfileValidator()
    {
        RuleFor(x => x.FirstName)
            .MaximumLength(80)
            .Matches(NameRegex)
                .WithMessage("Імʼя може містити лише літери, пробіли, дефіси та апострофи.")
            .When(x => !string.IsNullOrWhiteSpace(x.FirstName));

        RuleFor(x => x.LastName)
            .MaximumLength(80)
            .Matches(NameRegex)
                .WithMessage("Прізвище може містити лише літери, пробіли, дефіси та апострофи.")
            .When(x => !string.IsNullOrWhiteSpace(x.LastName));

        RuleFor(x => x.MiddleName)
            .MaximumLength(80)
            .Matches(NameRegex)
                .WithMessage("По-батькові може містити лише літери, пробіли, дефіси та апострофи.")
            .When(x => !string.IsNullOrWhiteSpace(x.MiddleName));

        RuleFor(x => x.Phone).MaximumLength(40).When(x => x.Phone is not null);

        RuleFor(x => x.DateOfBirth).Custom((dob, ctx) =>
        {
            if (dob is null) return;
            var today = DateOnly.FromDateTime(DateTime.UtcNow);
            if (dob.Value >= today)
            {
                ctx.AddFailure("DateOfBirth",
                    "Дата народження не може бути сьогодні або в майбутньому.");
                return;
            }
            if (dob.Value < today.AddYears(-130))
            {
                ctx.AddFailure("DateOfBirth", "Дата народження занадто давня.");
                return;
            }
            var minDob = today.AddYears(-MinAge);
            if (dob.Value > minDob)
            {
                ctx.AddFailure("DateOfBirth",
                    $"Вік має бути не менш ніж {MinAge} років.");
            }
        });

        RuleFor(x => x.HeightCm).InclusiveBetween(50, 250).When(x => x.HeightCm.HasValue);
        RuleFor(x => x.WeightKg).InclusiveBetween(20, 300).When(x => x.WeightKg.HasValue);
        RuleFor(x => x.WaistCm).InclusiveBetween(40, 250).When(x => x.WaistCm.HasValue);

        RuleFor(x => x.TypicalSystolicBp).InclusiveBetween(60, 250).When(x => x.TypicalSystolicBp.HasValue);
        RuleFor(x => x.TypicalDiastolicBp).InclusiveBetween(40, 200).When(x => x.TypicalDiastolicBp.HasValue);
        RuleFor(x => x.TypicalRestingPulse).InclusiveBetween(30, 200).When(x => x.TypicalRestingPulse.HasValue);

        RuleFor(x => x.ChronicDiseases).MaximumLength(4000).When(x => x.ChronicDiseases is not null);
        RuleFor(x => x.Allergies).MaximumLength(4000).When(x => x.Allergies is not null);
        RuleFor(x => x.CurrentMedications).MaximumLength(4000).When(x => x.CurrentMedications is not null);
        RuleFor(x => x.FamilyHistory).MaximumLength(4000).When(x => x.FamilyHistory is not null);

        RuleFor(x => x.EmergencyContactName).MaximumLength(160).When(x => x.EmergencyContactName is not null);
        RuleFor(x => x.EmergencyContactPhone).MaximumLength(40).When(x => x.EmergencyContactPhone is not null);
        RuleFor(x => x.EmergencyContactRelation).MaximumLength(80).When(x => x.EmergencyContactRelation is not null);

        RuleFor(x => x.PreferredLanguage).Must(l => l is "uk" or "en")
            .When(x => x.PreferredLanguage is not null)
            .WithMessage("Must be 'uk' or 'en'.");

        RuleFor(x => x.UnitsSystem).Must(u => u is "metric" or "imperial")
            .When(x => x.UnitsSystem is not null)
            .WithMessage("Must be 'metric' or 'imperial'.");
    }
}
