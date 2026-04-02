using HEMAX.Domain.Common;
using HEMAX.Domain.Enums;

namespace HEMAX.Domain.Entities;

/// <summary>JWT refresh token. Stored hashed for security.</summary>
public class RefreshToken
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid UserId { get; set; }
    public ApplicationUser? User { get; set; }

    public string TokenHash { get; set; } = string.Empty;

    public DateTimeOffset ExpiresAt { get; set; }
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    public bool IsRevoked { get; set; }
    public DateTimeOffset? RevokedAt { get; set; }
    public string? ReplacedByTokenHash { get; set; }

    public string? CreatedByIp  { get; set; }
    public string? UserAgent    { get; set; }

    public bool IsActive => !IsRevoked && DateTimeOffset.UtcNow < ExpiresAt;
}

public class Notification
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid UserId { get; set; }
    public ApplicationUser? User { get; set; }

    public NotificationType Type { get; set; }
    public string Title { get; set; } = string.Empty;

    [Encrypted]
    public string Body  { get; set; } = string.Empty;

    public string? Link { get; set; }

    public Guid? RelatedEntityId { get; set; }

    public bool IsRead { get; set; }
    public DateTimeOffset? ReadAt { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
}

public class AuditLog
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid? UserId { get; set; }
    public ApplicationUser? User { get; set; }

    public AuditAction Action { get; set; }

    public string? EntityType { get; set; }
    public Guid?   EntityId   { get; set; }

    [Encrypted]
    public string? DetailsJson { get; set; }

    public string? IpAddress { get; set; }
    public string? UserAgent { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
}

public class FileAsset
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid OwnerId { get; set; }
    public ApplicationUser? Owner { get; set; }

    public FileAssetType Type { get; set; }

    public string FileName { get; set; } = string.Empty;

    public string ContentType { get; set; } = string.Empty;
    public long   SizeBytes   { get; set; }

    public string StorageKey { get; set; } = string.Empty;

    public string? PublicUrl { get; set; }

    public Guid? RelatedEntityId { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
}

public class EmailVerification
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid UserId { get; set; }
    public ApplicationUser? User { get; set; }

    public string TokenHash { get; set; } = string.Empty;

    public DateTimeOffset ExpiresAt { get; set; }
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    public bool IsUsed { get; set; }
    public DateTimeOffset? UsedAt { get; set; }
}
