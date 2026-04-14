using System.Security.Claims;
using System.Text.Json;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using Microsoft.AspNetCore.Http;

namespace HEMAX.Infrastructure.Services;

public class SystemDateTimeProvider : IDateTimeProvider
{
    public DateTimeOffset UtcNow => DateTimeOffset.UtcNow;
    public DateOnly Today => DateOnly.FromDateTime(DateTime.UtcNow);
}

public class CurrentUserService : ICurrentUserService
{
    private readonly IHttpContextAccessor _http;

    public CurrentUserService(IHttpContextAccessor http) => _http = http;

    public Guid? UserId
    {
        get
        {
            var sub = _http.HttpContext?.User?.FindFirstValue(ClaimTypes.NameIdentifier);
            return Guid.TryParse(sub, out var id) ? id : null;
        }
    }

    public string? Email => _http.HttpContext?.User?.FindFirstValue(ClaimTypes.Email);

    public IReadOnlyList<string> Roles =>
        _http.HttpContext?.User?.FindAll(ClaimTypes.Role)
            .Select(c => c.Value)
            .ToList()
            .AsReadOnly()
        ?? (IReadOnlyList<string>)Array.Empty<string>();

    public bool IsAuthenticated =>
        _http.HttpContext?.User?.Identity?.IsAuthenticated ?? false;

    public bool IsInRole(string role) =>
        _http.HttpContext?.User?.IsInRole(role) ?? false;

    public string? IpAddress =>
        _http.HttpContext?.Connection?.RemoteIpAddress?.ToString();

    public string? UserAgent =>
        _http.HttpContext?.Request?.Headers["User-Agent"].ToString();
}

public class AuditService : IAuditService
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IDateTimeProvider _clock;

    public AuditService(IHemaxDbContext db, ICurrentUserService current, IDateTimeProvider clock)
    {
        _db = db; _current = current; _clock = clock;
    }

    public async Task LogAsync(
        AuditAction action, string? entityType = null, Guid? entityId = null,
        object? details = null, CancellationToken ct = default)
    {
        var entry = new AuditLog
        {
            UserId      = _current.UserId,
            Action      = action,
            EntityType  = entityType,
            EntityId    = entityId,
            DetailsJson = details is null ? null : JsonSerializer.Serialize(details),
            IpAddress   = _current.IpAddress,
            UserAgent   = _current.UserAgent,
            CreatedAt   = _clock.UtcNow,
        };

        _db.AuditLogs.Add(entry);
        await _db.SaveChangesAsync(ct);
    }
}

public class NotificationService : INotificationService
{
    private readonly IHemaxDbContext _db;

    public NotificationService(IHemaxDbContext db) => _db = db;

    public async Task NotifyAsync(
        Guid userId, NotificationType type, string title, string body,
        string? link = null, Guid? relatedEntityId = null,
        CancellationToken ct = default)
    {
        var n = new Notification
        {
            UserId          = userId,
            Type            = type,
            Title           = title,
            Body            = body,
            Link            = link,
            RelatedEntityId = relatedEntityId,
        };
        _db.Notifications.Add(n);
        await _db.SaveChangesAsync(ct);
    }
}
