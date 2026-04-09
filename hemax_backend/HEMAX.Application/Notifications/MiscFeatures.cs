using HEMAX.Application.Common.Models;
using HEMAX.Domain.Enums;
using MediatR;

namespace HEMAX.Application.Notifications
{
    public record NotificationDto(
        Guid Id,
        NotificationType Type,
        string Title,
        string Body,
        string? Link,
        Guid? RelatedEntityId,
        bool IsRead,
        DateTimeOffset CreatedAt
    );

    public record GetMyNotificationsQuery(
        bool? UnreadOnly,
        PageRequest Page
    ) : IRequest<PagedResult<NotificationDto>>;

    public record MarkNotificationReadCommand(
        Guid NotificationId
    ) : IRequest;

    public record MarkAllNotificationsReadCommand : IRequest;

    public record GetUnreadCountQuery : IRequest<int>;

}

namespace HEMAX.Application.Users
{
    using HEMAX.Application.Common.Models;
    using HEMAX.Domain.Enums;
    using MediatR;

    public record UpdateProfileCommand(
        string FirstName,
        string LastName,
        DateOnly? DateOfBirth,
        Sex Sex
    ) : IRequest;

    public record UpdateAvatarCommand(
        Stream FileStream,
        string FileName,
        string ContentType
    ) : IRequest<string>;  // returns new avatar URL

    public record GetAllUsersQuery(
        string? RoleFilter,
        string? Search,
        PageRequest Page
    ) : IRequest<PagedResult<HEMAX.Application.Auth.UserDto>>;

    public record SetUserBanStatusCommand(
        Guid UserId,
        bool IsBanned,
        string? Reason
    ) : IRequest;

    public record ChangeUserRoleCommand(
        Guid UserId,
        string NewRole
    ) : IRequest;
}


namespace HEMAX.Application.AuditLog
{
    using HEMAX.Application.Common.Models;
    using HEMAX.Domain.Enums;
    using MediatR;

    public record AuditLogDto(
        Guid Id,
        Guid? UserId,
        string? UserEmail,
        AuditAction Action,
        string? EntityType,
        Guid? EntityId,
        string? DetailsJson,
        string? IpAddress,
        DateTimeOffset CreatedAt
    );

    public record GetAuditLogQuery(
        Guid? UserId,
        AuditAction? Action,
        DateTimeOffset? From,
        DateTimeOffset? To,
        PageRequest Page
    ) : IRequest<PagedResult<AuditLogDto>>;
}
