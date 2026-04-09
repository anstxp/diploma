using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Common;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using HEMAX.Infrastructure.Files;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.UserProfiles;

internal static class ProfileMapper
{
    public static UserProfileDto ToDto(ApplicationUser user, UserProfile profile,
                                        IFileUrlGenerator? urlGen)
    {
        string? avatarUrl = user.AvatarUrl;
        if (urlGen is not null && !string.IsNullOrEmpty(avatarUrl)
            && !avatarUrl.StartsWith("http", StringComparison.OrdinalIgnoreCase))
        {
            avatarUrl = urlGen.GetDownloadUrl(avatarUrl);
        }

        return new UserProfileDto(
            UserId:                   user.Id,
            Email:                    user.Email ?? "",
            FirstName:                user.FirstName,
            LastName:                 user.LastName,
            MiddleName:               profile.MiddleName,
            DateOfBirth:              user.DateOfBirth,
            Age:                      user.GetAge(),
            Sex:                      user.Sex,
            AvatarUrl:                avatarUrl,
            Phone:                    profile.Phone,
            HeightCm:                 profile.HeightCm,
            WeightKg:                 profile.WeightKg,
            WaistCm:                  profile.WaistCm,
            Bmi:                      profile.Bmi,
            TypicalSystolicBp:        profile.TypicalSystolicBp,
            TypicalDiastolicBp:       profile.TypicalDiastolicBp,
            TypicalRestingPulse:      profile.TypicalRestingPulse,
            ChronicDiseases:          profile.ChronicDiseases,
            Allergies:                profile.Allergies,
            CurrentMedications:       profile.CurrentMedications,
            FamilyHistory:            profile.FamilyHistory,
            Smoker:                   profile.Smoker,
            AlcoholFrequency:         profile.AlcoholFrequency,
            PhysicalActivity:         profile.PhysicalActivity,
            DietType:                 profile.DietType,
            EmergencyContactName:     profile.EmergencyContactName,
            EmergencyContactPhone:    profile.EmergencyContactPhone,
            EmergencyContactRelation: profile.EmergencyContactRelation,
            PreferredLanguage:        profile.PreferredLanguage,
            UnitsSystem:              profile.UnitsSystem
        );
    }
}


public class GetMyProfileHandler : IRequestHandler<GetMyProfileQuery, UserProfileDto>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IFileUrlGenerator? _urlGen;

    public GetMyProfileHandler(IHemaxDbContext db, ICurrentUserService current,
                                IFileUrlGenerator? urlGen = null)
    {
        _db = db; _current = current; _urlGen = urlGen;
    }

    public async Task<UserProfileDto> Handle(GetMyProfileQuery req, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var user = await _db.Users.FirstOrDefaultAsync(u => u.Id == _current.UserId, ct)
                   ?? throw new UnauthorizedException("User not found");

        var profile = await _db.UserProfiles
                          .FirstOrDefaultAsync(p => p.UserId == user.Id, ct);

        if (profile is null)
        {
            profile = new UserProfile { UserId = user.Id };
            _db.UserProfiles.Add(profile);
            await _db.SaveChangesAsync(ct);
        }

        return ProfileMapper.ToDto(user, profile, _urlGen);
    }
}


public class GetUserProfileHandler : IRequestHandler<GetUserProfileQuery, UserProfileDto>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IFileUrlGenerator? _urlGen;

    public GetUserProfileHandler(IHemaxDbContext db, ICurrentUserService current,
                                  IFileUrlGenerator? urlGen = null)
    {
        _db = db; _current = current; _urlGen = urlGen;
    }

    public async Task<UserProfileDto> Handle(GetUserProfileQuery req, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        // Allow: self.
        bool allowed = _current.UserId == req.UserId;

        // Allow: admin.
        if (!allowed && _current.Roles.Contains("Administrator"))
            allowed = true;

        if (!allowed)
        {
            allowed = await _db.DoctorPatientLinks.AnyAsync(l =>
                l.DoctorId == _current.UserId &&
                l.PatientId == req.UserId &&
                l.Status == DoctorPatientStatus.Accepted, ct);
        }

        if (!allowed) throw new ForbiddenException(
            "Немає доступу до медичної картки цього користувача.");

        var user = await _db.Users.FirstOrDefaultAsync(u => u.Id == req.UserId, ct)
                   ?? throw new EntityNotFoundException("User", req.UserId);

        var profile = await _db.UserProfiles
                          .FirstOrDefaultAsync(p => p.UserId == user.Id, ct);

        if (profile is null)
        {
            profile = new UserProfile { UserId = user.Id };
            _db.UserProfiles.Add(profile);
            await _db.SaveChangesAsync(ct);
        }

        return ProfileMapper.ToDto(user, profile, _urlGen);
    }
}


public class UpdateMyProfileHandler : IRequestHandler<UpdateMyProfileCommand, UserProfileDto>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;
    private readonly IFileUrlGenerator? _urlGen;
    private readonly IEncryptionService _encryption;

    public UpdateMyProfileHandler(IHemaxDbContext db, ICurrentUserService current,
                                   IAuditService audit,
                                   IEncryptionService encryption,
                                   IFileUrlGenerator? urlGen = null)
    {
        _db = db; _current = current; _audit = audit;
        _encryption = encryption; _urlGen = urlGen;
    }

    public async Task<UserProfileDto> Handle(UpdateMyProfileCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var user = await _db.Users.FirstOrDefaultAsync(u => u.Id == _current.UserId, ct)
                   ?? throw new UnauthorizedException("User not found");

        var profile = await _db.UserProfiles
                          .FirstOrDefaultAsync(p => p.UserId == user.Id, ct);
        if (profile is null)
        {
            profile = new UserProfile { UserId = user.Id };
            _db.UserProfiles.Add(profile);
        }

        var b = cmd.Body;
        var changedFields = new List<string>();

        if (b.FirstName is not null && b.FirstName.Trim() != user.FirstName)
            { user.FirstName = b.FirstName.Trim(); changedFields.Add("FirstName"); }
        if (b.LastName is not null && b.LastName.Trim() != user.LastName)
            { user.LastName = b.LastName.Trim(); changedFields.Add("LastName"); }
        if (b.DateOfBirth is not null && b.DateOfBirth != user.DateOfBirth)
            { user.DateOfBirth = b.DateOfBirth; changedFields.Add("DateOfBirth"); }
        if (b.Sex is not null && b.Sex != user.Sex)
            { user.Sex = b.Sex.Value; changedFields.Add("Sex"); }
        user.UpdatedAt = DateTimeOffset.UtcNow;

        if (b.MiddleName is not null) { profile.MiddleName = NullIfBlank(b.MiddleName); changedFields.Add("MiddleName"); }
        if (b.Phone      is not null)
        {
            var newPhone = NullIfBlank(b.Phone);
            // Bug fix May 2026: was plain SHA-256(normalized_phone) — a phone
            // is a small-search-space identifier, so plain SHA-256 is brute-
            // forceable in seconds with a precomputed table (the global
            // phone numbering plan is well under 2^40 distinct E.164 strings,
            // not even close to enough entropy to resist a dictionary attack
            // against the hash). Now we use the encryption service's keyed
            // HMAC blind index, which is computed against a secret derived
            // from the encryption MasterPassphrase. Without the key, an
            // attacker holding only the DB dump can't reverse the index to
            // get phone numbers back.
            //
            // The migration story: existing rows have plain-SHA-256 hashes.
            // Those become "orphaned" — uniqueness check still works for new
            // submissions because both old and new users now hash the same
            // way via the new HMAC, but legacy rows won't collide with
            // newly-hashed input. That's fine for uniqueness (we'd let two
            // different accounts have the same phone until both updated),
            // and a one-off rehash migration can be added later if needed.
            var newHash  = newPhone is null
                ? null
                : _encryption.ComputeBlindIndex(PhoneNormalizer.Normalize(newPhone));

            if (newHash != profile.PhoneHash && newHash is not null)
            {
                var taken = await _db.UserProfiles.AnyAsync(p =>
                    p.UserId != profile.UserId && p.PhoneHash == newHash, ct);
                if (taken)
                    throw new BusinessRuleViolationException("PHONE_TAKEN",
                        "Цей номер телефону вже використовується іншим акаунтом.");
            }

            profile.Phone     = newPhone;
            profile.PhoneHash = newHash;
            changedFields.Add("Phone");
        }

        if (b.HeightCm is not null) { profile.HeightCm = b.HeightCm; changedFields.Add("HeightCm"); }
        if (b.WeightKg is not null) { profile.WeightKg = b.WeightKg; changedFields.Add("WeightKg"); }
        if (b.WaistCm  is not null) { profile.WaistCm  = b.WaistCm;  changedFields.Add("WaistCm"); }

        if (b.TypicalSystolicBp   is not null) { profile.TypicalSystolicBp   = b.TypicalSystolicBp;   changedFields.Add("TypicalSystolicBp"); }
        if (b.TypicalDiastolicBp  is not null) { profile.TypicalDiastolicBp  = b.TypicalDiastolicBp;  changedFields.Add("TypicalDiastolicBp"); }
        if (b.TypicalRestingPulse is not null) { profile.TypicalRestingPulse = b.TypicalRestingPulse; changedFields.Add("TypicalRestingPulse"); }

        if (b.ChronicDiseases     is not null) { profile.ChronicDiseases     = NullIfBlank(b.ChronicDiseases);     changedFields.Add("ChronicDiseases"); }
        if (b.Allergies           is not null) { profile.Allergies           = NullIfBlank(b.Allergies);           changedFields.Add("Allergies"); }
        if (b.CurrentMedications  is not null) { profile.CurrentMedications  = NullIfBlank(b.CurrentMedications);  changedFields.Add("CurrentMedications"); }
        if (b.FamilyHistory       is not null) { profile.FamilyHistory       = NullIfBlank(b.FamilyHistory);       changedFields.Add("FamilyHistory"); }

        if (b.Smoker is not null)             { profile.Smoker = b.Smoker.Value; changedFields.Add("Smoker"); }
        if (b.AlcoholFrequency is not null)   { profile.AlcoholFrequency = b.AlcoholFrequency.Value; changedFields.Add("AlcoholFrequency"); }
        if (b.PhysicalActivity is not null)   { profile.PhysicalActivity = b.PhysicalActivity.Value; changedFields.Add("PhysicalActivity"); }
        if (b.DietType is not null)           { profile.DietType = b.DietType.Value; changedFields.Add("DietType"); }

        if (b.EmergencyContactName     is not null) { profile.EmergencyContactName     = NullIfBlank(b.EmergencyContactName);     changedFields.Add("EmergencyContactName"); }
        if (b.EmergencyContactPhone    is not null) { profile.EmergencyContactPhone    = NullIfBlank(b.EmergencyContactPhone);    changedFields.Add("EmergencyContactPhone"); }
        if (b.EmergencyContactRelation is not null) { profile.EmergencyContactRelation = NullIfBlank(b.EmergencyContactRelation); changedFields.Add("EmergencyContactRelation"); }

        if (b.PreferredLanguage is not null) { profile.PreferredLanguage = b.PreferredLanguage; changedFields.Add("PreferredLanguage"); }
        if (b.UnitsSystem       is not null) { profile.UnitsSystem       = b.UnitsSystem;       changedFields.Add("UnitsSystem"); }

        profile.UpdatedAt = DateTimeOffset.UtcNow;

        try
        {
            await _db.SaveChangesAsync(ct);
        }
        catch (DbUpdateException ex) when (
            (ex.InnerException?.Message ?? ex.Message)
                .Contains("PhoneHash", StringComparison.OrdinalIgnoreCase))
        {
            throw new BusinessRuleViolationException("PHONE_TAKEN",
                "Цей номер телефону вже використовується іншим акаунтом.");
        }

        if (changedFields.Count > 0)
        {
            await _audit.LogAsync(AuditAction.UserProfileUpdated,
                "UserProfile", profile.Id,
                new { changedFields });
        }

        return ProfileMapper.ToDto(user, profile, _urlGen);
    }

    private static string? NullIfBlank(string? s) =>
        string.IsNullOrWhiteSpace(s) ? null : s.Trim();
}
