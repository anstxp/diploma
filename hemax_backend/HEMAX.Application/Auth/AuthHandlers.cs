using System.Security.Cryptography;
using System.Text;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Common;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace HEMAX.Application.Auth;


public class RegisterCommandHandler : IRequestHandler<RegisterCommand, Guid>
{
    private readonly IIdentityService _identity;
    private readonly IHemaxDbContext _db;
    private readonly IEmailService _email;
    private readonly IDateTimeProvider _clock;
    private readonly IAuditService _audit;
    private readonly IConfiguration _config;
    private readonly ILogger<RegisterCommandHandler> _logger;
    private readonly IEncryptionService _encryption;

    public RegisterCommandHandler(
        IIdentityService identity,
        IHemaxDbContext db,
        IEmailService email,
        IDateTimeProvider clock,
        IAuditService audit,
        IConfiguration config,
        IEncryptionService encryption,
        ILogger<RegisterCommandHandler> logger)
    {
        _identity = identity;
        _db = db;
        _email = email;
        _clock = clock;
        _audit = audit;
        _config = config;
        _encryption = encryption;
        _logger = logger;
    }

    public async Task<Guid> Handle(RegisterCommand cmd, CancellationToken ct)
    {
        // ── Pre-flight: phone must be unique ────────────────────────
        // The encrypted Phone column can't be queried by value (random nonces),
        // so we keep a deterministic hash alongside it.
        //
        // Bug fix May 2026: was plain SHA-256(normalized_phone) — brute-
        // forceable in seconds with a precomputed table because the global
        // phone numbering plan has far too little entropy to resist a
        // dictionary attack. Now we use the keyed HMAC blind index via
        // IEncryptionService.ComputeBlindIndex. Without the secret key
        // (derived from Encryption.MasterPassphrase), an attacker holding
        // only the DB dump can't reverse the index back to phone numbers.
        var normalizedPhone = PhoneNormalizer.Normalize(cmd.Phone);
        if (string.IsNullOrEmpty(normalizedPhone))
            throw new BusinessRuleViolationException("PHONE_REQUIRED",
                "Телефон обов'язковий.");

        var phoneHash = _encryption.ComputeBlindIndex(normalizedPhone);

        var phoneTaken = await _db.UserProfiles
            .AnyAsync(p => p.PhoneHash == phoneHash, ct);
        if (phoneTaken)
            throw new BusinessRuleViolationException("PHONE_TAKEN",
                "Цей номер телефону вже використовується іншим акаунтом.");

        var (success, errors, user) = await _identity.RegisterAsync(
            cmd.Email, cmd.Password, cmd.FirstName, cmd.LastName,
            cmd.DateOfBirth, cmd.Sex, ct);

        if (!success || user is null)
            throw new BusinessRuleViolationException("REGISTER_FAILED", string.Join("; ", errors));

        // Default role
        await _identity.AddToRoleAsync(user, Roles.User, ct);

        var profile = new UserProfile
        {
            UserId                   = user.Id,
            Phone                    = cmd.Phone?.Trim(),
            PhoneHash                = phoneHash,
            MiddleName               = string.IsNullOrWhiteSpace(cmd.MiddleName) ? null : cmd.MiddleName.Trim(),
            HeightCm                 = cmd.HeightCm,
            WeightKg                 = cmd.WeightKg,
            WaistCm                  = cmd.WaistCm,
            TypicalSystolicBp        = cmd.TypicalSystolicBp,
            TypicalDiastolicBp       = cmd.TypicalDiastolicBp,
            TypicalRestingPulse      = cmd.TypicalRestingPulse,
            Smoker                   = cmd.Smoker ?? false,
            AlcoholFrequency         = cmd.AlcoholFrequency ?? Domain.Enums.AlcoholFrequency.Unknown,
            PhysicalActivity         = cmd.PhysicalActivity ?? Domain.Enums.PhysicalActivity.Unknown,
            DietType                 = cmd.DietType ?? Domain.Enums.DietType.Unknown,
            ChronicDiseases          = string.IsNullOrWhiteSpace(cmd.ChronicDiseases)    ? null : cmd.ChronicDiseases.Trim(),
            Allergies                = string.IsNullOrWhiteSpace(cmd.Allergies)          ? null : cmd.Allergies.Trim(),
            CurrentMedications       = string.IsNullOrWhiteSpace(cmd.CurrentMedications) ? null : cmd.CurrentMedications.Trim(),
            FamilyHistory            = string.IsNullOrWhiteSpace(cmd.FamilyHistory)      ? null : cmd.FamilyHistory.Trim(),
            EmergencyContactName     = string.IsNullOrWhiteSpace(cmd.EmergencyContactName)     ? null : cmd.EmergencyContactName.Trim(),
            EmergencyContactPhone    = string.IsNullOrWhiteSpace(cmd.EmergencyContactPhone)    ? null : cmd.EmergencyContactPhone.Trim(),
            EmergencyContactRelation = string.IsNullOrWhiteSpace(cmd.EmergencyContactRelation) ? null : cmd.EmergencyContactRelation.Trim(),
            PreferredLanguage        = string.IsNullOrWhiteSpace(cmd.PreferredLanguage) ? "uk" : cmd.PreferredLanguage.Trim(),
            UnitsSystem              = string.IsNullOrWhiteSpace(cmd.UnitsSystem) ? "metric" : cmd.UnitsSystem.Trim(),
        };
        _db.UserProfiles.Add(profile);
        try
        {
            await _db.SaveChangesAsync(ct);
        }
        catch (DbUpdateException ex) when (IsPhoneUniqueViolation(ex))
        {
            throw new BusinessRuleViolationException("PHONE_TAKEN",
                "Цей номер телефону вже використовується іншим акаунтом.");
        }


        // Email verification token
        var rawToken  = GenerateToken();
        var hashed    = HashToken(rawToken);
        var verification = new EmailVerification
        {
            UserId    = user.Id,
            TokenHash = hashed,
            ExpiresAt = _clock.UtcNow.AddHours(24),
        };
        _db.EmailVerifications.Add(verification);
        await _db.SaveChangesAsync(ct);

        // Send verification email
        var baseUrl = _config["App:BaseUrl"] ?? "https://localhost:5001";
        var link = $"{baseUrl}/api/auth/verify?userId={user.Id}&token={rawToken}";

        try
        {
            await _email.SendEmailVerificationAsync(cmd.Email, link, ct);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to send verification email to {Email}", cmd.Email);
        }

        await _audit.LogAsync(AuditAction.Register, "User", user.Id, new { user.Email }, ct);

        return user.Id;
    }

    private static string GenerateToken() =>
        Convert.ToBase64String(RandomNumberGenerator.GetBytes(32))
               .Replace("+", "-").Replace("/", "_").TrimEnd('=');

    private static string HashToken(string raw)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(raw));
        return Convert.ToHexString(bytes);
    }

    private static bool IsPhoneUniqueViolation(DbUpdateException ex)
    {
        var msg = (ex.InnerException?.Message ?? ex.Message);
        return msg.Contains("IX_UserProfiles_PhoneHash_Unique", StringComparison.OrdinalIgnoreCase)
            || msg.Contains("PhoneHash", StringComparison.OrdinalIgnoreCase);
    }
}


public class LoginCommandHandler : IRequestHandler<LoginCommand, AuthTokensDto>
{
    private readonly IIdentityService _identity;
    private readonly ITokenService _tokens;
    private readonly IHemaxDbContext _db;
    private readonly IDateTimeProvider _clock;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;
    private readonly IConfiguration _config;

    public LoginCommandHandler(
        IIdentityService identity, ITokenService tokens, IHemaxDbContext db,
        IDateTimeProvider clock, ICurrentUserService current, IAuditService audit,
        IConfiguration config)
    {
        _identity = identity;
        _tokens = tokens;
        _db = db;
        _clock = clock;
        _current = current;
        _audit = audit;
        _config = config;
    }

    public async Task<AuthTokensDto> Handle(LoginCommand cmd, CancellationToken ct)
    {
        var (ok, user) = await _identity.ValidateCredentialsAsync(cmd.Email, cmd.Password, ct);
        if (!ok || user is null)
            throw new UnauthorizedException("Invalid email or password");

        if (user.IsBanned)
            throw new ForbiddenException(user.BanReason ?? "Account is banned");

        var roles = await _identity.GetUserRolesAsync(user, ct);

        var accessToken      = _tokens.CreateAccessToken(user, roles);
        var refreshTokenRaw  = _tokens.CreateRefreshToken();
        var refreshTokenHash = _tokens.HashRefreshToken(refreshTokenRaw);

        var refreshExpDays = int.Parse(_config["Jwt:RefreshTokenExpirationDays"] ?? "7");
        var accessExpMin   = int.Parse(_config["Jwt:AccessTokenExpirationMinutes"] ?? "15");

        var refreshEntity = new RefreshToken
        {
            UserId      = user.Id,
            TokenHash   = refreshTokenHash,
            ExpiresAt   = _clock.UtcNow.AddDays(refreshExpDays),
            CreatedByIp = _current.IpAddress,
            UserAgent   = _current.UserAgent,
        };
        _db.RefreshTokens.Add(refreshEntity);
        await _db.SaveChangesAsync(ct);

        await _audit.LogAsync(AuditAction.Login, "User", user.Id, null, ct);

        return new AuthTokensDto(
            AccessToken:           accessToken,
            RefreshToken:          refreshTokenRaw,
            AccessTokenExpiresAt:  _clock.UtcNow.AddMinutes(accessExpMin),
            RefreshTokenExpiresAt: refreshEntity.ExpiresAt,
            User: new UserDto(
                user.Id, user.Email!, user.FirstName, user.LastName,
                user.DateOfBirth, user.Sex, user.AvatarUrl,
                roles.ToList().AsReadOnly(),
                user.EmailConfirmed, user.CreatedAt
            )
        );
    }
}


public class RefreshTokensCommandHandler : IRequestHandler<RefreshTokensCommand, AuthTokensDto>
{
    private readonly IIdentityService _identity;
    private readonly ITokenService _tokens;
    private readonly IHemaxDbContext _db;
    private readonly IDateTimeProvider _clock;
    private readonly ICurrentUserService _current;
    private readonly IConfiguration _config;

    public RefreshTokensCommandHandler(
        IIdentityService identity, ITokenService tokens, IHemaxDbContext db,
        IDateTimeProvider clock, ICurrentUserService current, IConfiguration config)
    {
        _identity = identity;
        _tokens = tokens;
        _db = db;
        _clock = clock;
        _current = current;
        _config = config;
    }

    public async Task<AuthTokensDto> Handle(RefreshTokensCommand cmd, CancellationToken ct)
    {
        var hashed = _tokens.HashRefreshToken(cmd.RefreshToken);

        var entity = await _db.RefreshTokens
            .Include(rt => rt.User)
            .FirstOrDefaultAsync(rt => rt.TokenHash == hashed, ct);

        if (entity is null || !entity.IsActive)
            throw new UnauthorizedException("Invalid or expired refresh token");

        // Rotate: revoke old, issue new
        var newRaw  = _tokens.CreateRefreshToken();
        var newHash = _tokens.HashRefreshToken(newRaw);

        entity.IsRevoked = true;
        entity.RevokedAt = _clock.UtcNow;
        entity.ReplacedByTokenHash = newHash;

        var refreshExpDays = int.Parse(_config["Jwt:RefreshTokenExpirationDays"] ?? "7");
        var accessExpMin   = int.Parse(_config["Jwt:AccessTokenExpirationMinutes"] ?? "15");

        var newEntity = new RefreshToken
        {
            UserId      = entity.UserId,
            TokenHash   = newHash,
            ExpiresAt   = _clock.UtcNow.AddDays(refreshExpDays),
            CreatedByIp = _current.IpAddress,
            UserAgent   = _current.UserAgent,
        };
        _db.RefreshTokens.Add(newEntity);
        await _db.SaveChangesAsync(ct);

        var user  = entity.User!;
        var roles = await _identity.GetUserRolesAsync(user, ct);
        var access = _tokens.CreateAccessToken(user, roles);

        return new AuthTokensDto(
            AccessToken:           access,
            RefreshToken:          newRaw,
            AccessTokenExpiresAt:  _clock.UtcNow.AddMinutes(accessExpMin),
            RefreshTokenExpiresAt: newEntity.ExpiresAt,
            User: new UserDto(
                user.Id, user.Email!, user.FirstName, user.LastName,
                user.DateOfBirth, user.Sex, user.AvatarUrl,
                roles.ToList().AsReadOnly(),
                user.EmailConfirmed, user.CreatedAt
            )
        );
    }
}


public class LogoutCommandHandler : IRequestHandler<LogoutCommand>
{
    private readonly ITokenService _tokens;
    private readonly IHemaxDbContext _db;
    private readonly IDateTimeProvider _clock;
    private readonly IAuditService _audit;
    private readonly ICurrentUserService _current;

    public LogoutCommandHandler(ITokenService tokens, IHemaxDbContext db,
        IDateTimeProvider clock, IAuditService audit, ICurrentUserService current)
    {
        _tokens = tokens; _db = db; _clock = clock;
        _audit = audit; _current = current;
    }

    public async Task Handle(LogoutCommand cmd, CancellationToken ct)
    {
        var hashed = _tokens.HashRefreshToken(cmd.RefreshToken);
        var entity = await _db.RefreshTokens.FirstOrDefaultAsync(
            rt => rt.TokenHash == hashed, ct);

        if (entity is { IsRevoked: false })
        {
            entity.IsRevoked = true;
            entity.RevokedAt = _clock.UtcNow;
            await _db.SaveChangesAsync(ct);

            if (_current.UserId is not null)
                await _audit.LogAsync(AuditAction.Logout, "User", _current.UserId, null, ct);
        }
    }
}


public class VerifyEmailCommandHandler : IRequestHandler<VerifyEmailCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly IDateTimeProvider _clock;
    private readonly IIdentityService _identity;

    public VerifyEmailCommandHandler(IHemaxDbContext db, IDateTimeProvider clock,
        IIdentityService identity)
    {
        _db = db; _clock = clock; _identity = identity;
    }

    public async Task Handle(VerifyEmailCommand cmd, CancellationToken ct)
    {
        var hashed = HashToken(cmd.Token);

        var ev = await _db.EmailVerifications
            .Where(v => v.UserId == cmd.UserId && v.TokenHash == hashed && !v.IsUsed)
            .FirstOrDefaultAsync(ct);

        if (ev is null || ev.ExpiresAt < _clock.UtcNow)
            throw new BusinessRuleViolationException("VERIFICATION_INVALID",
                "Invalid or expired verification token");

        ev.IsUsed = true;
        ev.UsedAt = _clock.UtcNow;

        var user = await _identity.GetUserByIdAsync(cmd.UserId, ct);
        if (user is not null)
        {
            user.EmailConfirmed = true;
        }

        await _db.SaveChangesAsync(ct);
    }

    private static string HashToken(string raw)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(raw));
        return Convert.ToHexString(bytes);
    }
}


public class GetMeQueryHandler : IRequestHandler<GetMeQuery, UserDto>
{
    private readonly ICurrentUserService _current;
    private readonly IIdentityService _identity;

    public GetMeQueryHandler(ICurrentUserService current, IIdentityService identity)
    {
        _current = current; _identity = identity;
    }

    public async Task<UserDto> Handle(GetMeQuery query, CancellationToken ct)
    {
        if (_current.UserId is null)
            throw new UnauthorizedException();

        var user = await _identity.GetUserByIdAsync(_current.UserId.Value, ct)
            ?? throw new UnauthorizedException();
        var roles = await _identity.GetUserRolesAsync(user, ct);

        return new UserDto(
            user.Id, user.Email!, user.FirstName, user.LastName,
            user.DateOfBirth, user.Sex, user.AvatarUrl,
            roles.ToList().AsReadOnly(), user.EmailConfirmed, user.CreatedAt
        );
    }
}


public class ChangePasswordCommandHandler : IRequestHandler<ChangePasswordCommand>
{
    private readonly IIdentityService _identity;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;

    public ChangePasswordCommandHandler(
        IIdentityService identity, ICurrentUserService current, IAuditService audit)
    {
        _identity = identity; _current = current; _audit = audit;
    }

    public async Task Handle(ChangePasswordCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var ok = await _identity.ChangePasswordAsync(
            _current.UserId.Value, cmd.CurrentPassword, cmd.NewPassword, ct);

        if (!ok)
            throw new BusinessRuleViolationException("PASSWORD_CHANGE_FAILED",
                "Current password is incorrect or new password fails policy");

        await _audit.LogAsync(AuditAction.PasswordChanged, "User", _current.UserId, null, ct);
    }
}
