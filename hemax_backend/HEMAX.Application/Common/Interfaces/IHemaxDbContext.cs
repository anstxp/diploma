using HEMAX.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Common.Interfaces;

public interface IHemaxDbContext
{
    DbSet<Analysis>           Analyses           { get; }
    DbSet<BlogPost>           BlogPosts          { get; }
    DbSet<Comment>            Comments           { get; }
    DbSet<PostLike>           PostLikes          { get; }
    DbSet<DoctorPatientLink>  DoctorPatientLinks { get; }
    DbSet<RefreshToken>       RefreshTokens      { get; }
    DbSet<Notification>       Notifications      { get; }
    DbSet<Domain.Entities.AuditLog>           AuditLogs          { get; }
    DbSet<FileAsset>          FileAssets         { get; }
    DbSet<UserProfile>        UserProfiles       { get; }
    DbSet<EmailVerification>  EmailVerifications { get; }
    DbSet<ApplicationUser>    Users              { get; }

    Task<int> SaveChangesAsync(CancellationToken ct = default);
}

public interface ICurrentUserService
{
    Guid? UserId { get; }
    string? Email { get; }
    IReadOnlyList<string> Roles { get; }
    bool IsAuthenticated { get; }
    bool IsInRole(string role);
    string? IpAddress { get; }
    string? UserAgent { get; }
}

public interface ITokenService
{
    string CreateAccessToken(ApplicationUser user, IEnumerable<string> roles);
    string CreateRefreshToken();
    string HashRefreshToken(string rawToken);
}

public interface IIdentityService
{
    Task<(bool Success, string[] Errors, ApplicationUser? User)> RegisterAsync(
        string email, string password, string firstName, string lastName,
        DateOnly? dob, Domain.Enums.Sex sex, CancellationToken ct);

    Task<(bool Success, ApplicationUser? User)> ValidateCredentialsAsync(
        string email, string password, CancellationToken ct);

    Task<IList<string>> GetUserRolesAsync(ApplicationUser user, CancellationToken ct);

    Task AddToRoleAsync(ApplicationUser user, string role, CancellationToken ct);

    Task<bool> ChangePasswordAsync(
        Guid userId, string currentPassword, string newPassword, CancellationToken ct);

    Task<ApplicationUser?> GetUserByEmailAsync(string email, CancellationToken ct);
    Task<ApplicationUser?> GetUserByIdAsync(Guid id, CancellationToken ct);
}

public interface IEmailService
{
    Task SendEmailVerificationAsync(string toEmail, string verificationLink, CancellationToken ct);
    Task SendDoctorInviteAsync(string toEmail, string doctorName, string acceptLink, CancellationToken ct);
    Task SendPasswordResetAsync(string toEmail, string resetLink, CancellationToken ct);
}

public interface IFileStorageService
{
    Task<(string StorageKey, string? PublicUrl)> SaveAsync(
        Stream content, string fileName, string contentType,
        CancellationToken ct, string? category = null);

    Task<Stream> OpenReadAsync(string storageKey, CancellationToken ct);

    Task DeleteAsync(string storageKey, CancellationToken ct);
}

public interface IDateTimeProvider
{
    DateTimeOffset UtcNow { get; }
    DateOnly Today { get; }
}

public interface INotificationService
{
    Task NotifyAsync(
        Guid userId,
        Domain.Enums.NotificationType type,
        string title,
        string body,
        string? link = null,
        Guid? relatedEntityId = null,
        CancellationToken ct = default);
}

/// <summary>Audit logger.</summary>
public interface IAuditService
{
    Task LogAsync(
        Domain.Enums.AuditAction action,
        string? entityType = null,
        Guid? entityId = null,
        object? details = null,
        CancellationToken ct = default);
}
