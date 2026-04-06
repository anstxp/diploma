using HEMAX.Domain.Enums;
using MediatR;

namespace HEMAX.Application.Auth;

public record AuthTokensDto(
    string AccessToken,
    string RefreshToken,
    DateTimeOffset AccessTokenExpiresAt,
    DateTimeOffset RefreshTokenExpiresAt,
    UserDto User
);

public record UserDto(
    Guid Id,
    string Email,
    string FirstName,
    string LastName,
    DateOnly? DateOfBirth,
    Sex Sex,
    string? AvatarUrl,
    IReadOnlyList<string> Roles,
    bool EmailConfirmed,
    DateTimeOffset CreatedAt
);

public record RegisterCommand(
    string Email,
    string Password,
    string FirstName,
    string LastName,
    DateOnly? DateOfBirth,
    Sex Sex,
    string Phone,
    string? MiddleName        = null,
    double? HeightCm          = null,
    double? WeightKg          = null,
    double? WaistCm           = null,
    double? TypicalSystolicBp = null,
    double? TypicalDiastolicBp = null,
    double? TypicalRestingPulse = null,
    bool?   Smoker            = null,
    AlcoholFrequency? AlcoholFrequency = null,
    PhysicalActivity? PhysicalActivity = null,
    DietType? DietType                 = null,
    string? ChronicDiseases   = null,
    string? Allergies         = null,
    string? CurrentMedications = null,
    string? FamilyHistory     = null,
    string? EmergencyContactName     = null,
    string? EmergencyContactPhone    = null,
    string? EmergencyContactRelation = null,
    string? PreferredLanguage = null,
    string? UnitsSystem       = null
) : IRequest<Guid>;

public record LoginCommand(
    string Email,
    string Password
) : IRequest<AuthTokensDto>;

public record RefreshTokensCommand(
    string RefreshToken
) : IRequest<AuthTokensDto>;

public record LogoutCommand(
    string RefreshToken
) : IRequest;

public record VerifyEmailCommand(
    Guid UserId,
    string Token
) : IRequest;

public record ResendVerificationEmailCommand(
    string Email
) : IRequest;

public record ChangePasswordCommand(
    string CurrentPassword,
    string NewPassword
) : IRequest;


public record GetMeQuery : IRequest<UserDto>;
