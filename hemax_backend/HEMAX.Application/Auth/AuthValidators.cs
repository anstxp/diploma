using FluentValidation;
using HEMAX.Domain.Enums;

namespace HEMAX.Application.Auth;

public class RegisterCommandValidator : AbstractValidator<RegisterCommand>
{
    public const string NameRegex = @"^[\p{L}\p{M}\s'\u2019\-]+$";

    public const int MinRegistrationAge = 13;

    public RegisterCommandValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty()
            .EmailAddress()
            .MaximumLength(256);

        RuleFor(x => x.Password)
            .NotEmpty()
            .MinimumLength(8)
            .MaximumLength(128)
            .Matches(@"[A-Z]").WithMessage("Password must contain at least one uppercase letter")
            .Matches(@"[a-z]").WithMessage("Password must contain at least one lowercase letter")
            .Matches(@"[0-9]").WithMessage("Password must contain at least one digit");

        RuleFor(x => x.FirstName)
            .NotEmpty().WithMessage("Імʼя обовʼязкове.")
            .MaximumLength(80)
            .Matches(NameRegex)
                .WithMessage("Імʼя може містити лише літери, пробіли, дефіси та апострофи.");

        RuleFor(x => x.LastName)
            .NotEmpty().WithMessage("Прізвище обовʼязкове.")
            .MaximumLength(80)
            .Matches(NameRegex)
                .WithMessage("Прізвище може містити лише літери, пробіли, дефіси та апострофи.");

        // Step-1 required identity fields
        RuleFor(x => x.DateOfBirth)
            .NotNull().WithMessage("Дата народження обовʼязкова.")
            .Custom((dob, ctx) =>
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
                var minDob = today.AddYears(-MinRegistrationAge);
                if (dob.Value > minDob)
                {
                    var age = today.Year - dob.Value.Year
                        - (dob.Value > today.AddYears(-(today.Year - dob.Value.Year)) ? 1 : 0);
                    ctx.AddFailure("DateOfBirth",
                        $"Реєстрація з віку {MinRegistrationAge} років. Зараз вам {age}.");
                }
            });

        RuleFor(x => x.Sex)
            .NotEqual(Sex.Unknown).WithMessage("Стать обовʼязкова.")
            .IsInEnum();

        RuleFor(x => x.Phone)
            .NotEmpty().WithMessage("Телефон обовʼязковий.")
            .MaximumLength(40)
            .Matches(@"^[\+\d\s\-\(\)]{6,40}$")
                .WithMessage("Телефон має містити лише цифри, +, пробіли, дефіси, дужки.");

        RuleFor(x => x.MiddleName)
            .MaximumLength(80)
            .Matches(NameRegex)
                .WithMessage("По-батькові може містити лише літери, пробіли, дефіси та апострофи.")
            .When(x => !string.IsNullOrWhiteSpace(x.MiddleName));

        RuleFor(x => x.EmergencyContactName)
            .MaximumLength(160)
            .Matches(NameRegex)
                .WithMessage("Імʼя контакту може містити лише літери, пробіли, дефіси та апострофи.")
            .When(x => !string.IsNullOrWhiteSpace(x.EmergencyContactName));

        RuleFor(x => x.HeightCm).InclusiveBetween(50, 250).When(x => x.HeightCm.HasValue);
        RuleFor(x => x.WeightKg).InclusiveBetween(20, 300).When(x => x.WeightKg.HasValue);
        RuleFor(x => x.WaistCm).InclusiveBetween(30, 250).When(x => x.WaistCm.HasValue);

        RuleFor(x => x.TypicalSystolicBp).InclusiveBetween(60, 250).When(x => x.TypicalSystolicBp.HasValue);
        RuleFor(x => x.TypicalDiastolicBp).InclusiveBetween(30, 150).When(x => x.TypicalDiastolicBp.HasValue);
        RuleFor(x => x.TypicalRestingPulse).InclusiveBetween(30, 200).When(x => x.TypicalRestingPulse.HasValue);

        RuleFor(x => x.PreferredLanguage)
            .Must(v => v is "uk" or "en")
                .WithMessage("Supported languages: uk, en")
            .When(x => !string.IsNullOrWhiteSpace(x.PreferredLanguage));

        RuleFor(x => x.UnitsSystem)
            .Must(v => v is "metric" or "imperial")
                .WithMessage("Supported units: metric, imperial")
            .When(x => !string.IsNullOrWhiteSpace(x.UnitsSystem));

        RuleFor(x => x.ChronicDiseases).MaximumLength(4000).When(x => x.ChronicDiseases is not null);
        RuleFor(x => x.Allergies).MaximumLength(4000).When(x => x.Allergies is not null);
        RuleFor(x => x.CurrentMedications).MaximumLength(4000).When(x => x.CurrentMedications is not null);
        RuleFor(x => x.FamilyHistory).MaximumLength(4000).When(x => x.FamilyHistory is not null);

        RuleFor(x => x.EmergencyContactPhone).MaximumLength(40).When(x => x.EmergencyContactPhone is not null);
        RuleFor(x => x.EmergencyContactRelation).MaximumLength(80).When(x => x.EmergencyContactRelation is not null);
    }
}

public class LoginCommandValidator : AbstractValidator<LoginCommand>
{
    public LoginCommandValidator()
    {
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        RuleFor(x => x.Password).NotEmpty();
    }
}

public class RefreshTokensCommandValidator : AbstractValidator<RefreshTokensCommand>
{
    public RefreshTokensCommandValidator()
    {
        RuleFor(x => x.RefreshToken).NotEmpty();
    }
}

public class ChangePasswordCommandValidator : AbstractValidator<ChangePasswordCommand>
{
    public ChangePasswordCommandValidator()
    {
        RuleFor(x => x.CurrentPassword).NotEmpty();
        RuleFor(x => x.NewPassword)
            .NotEmpty()
            .MinimumLength(8)
            .Matches(@"[A-Z]").Matches(@"[a-z]").Matches(@"[0-9]");

        RuleFor(x => x)
            .Must(x => x.CurrentPassword != x.NewPassword)
            .WithMessage("New password must differ from current password");
    }
}

public class VerifyEmailCommandValidator : AbstractValidator<VerifyEmailCommand>
{
    public VerifyEmailCommandValidator()
    {
        RuleFor(x => x.UserId).NotEmpty();
        RuleFor(x => x.Token).NotEmpty();
    }
}
