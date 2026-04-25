using HEMAX.Application.AuditLog;
using HEMAX.Application.Auth;
using HEMAX.Application.BlogPosts;
using HEMAX.Application.Common.Models;
using HEMAX.Application.DoctorPatient;
using HEMAX.Application.Notifications;
using HEMAX.Application.Users;
using HEMAX.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace HEMAX.Web.Controllers;


[ApiController]
[Route("api/doctors")]
[Authorize]
public class DoctorsController : ControllerBase
{
    private readonly IMediator _mediator;
    public DoctorsController(IMediator mediator) => _mediator = mediator;

    [Authorize(Roles = Roles.Doctor)]
    [HttpPost("invites")]
    public async Task<ActionResult<Guid>> Invite(
        [FromBody] InvitePatientCommand cmd, CancellationToken ct)
    {
        var id = await _mediator.Send(cmd, ct);
        return Ok(new { id });
    }

    [HttpGet("invites")]
    public async Task<ActionResult<PagedResult<DoctorPatientLinkDto>>> MyIncomingInvites(
        [FromQuery] int page = 1, [FromQuery] int pageSize = 50,
        CancellationToken ct = default)
        => Ok(await _mediator.Send(
            new GetMyDoctorsQuery(DoctorPatientStatus.Pending,
                new PageRequest { Page = page, PageSize = pageSize }), ct));

    [HttpPost("invites/{linkId:guid}/respond")]
    public async Task<IActionResult> Respond(
        Guid linkId, [FromBody] RespondBody body, CancellationToken ct)
    {
        await _mediator.Send(
            new RespondToDoctorRequestCommand(linkId, body.Accept, body.Note), ct);
        return NoContent();
    }

    [HttpDelete("links/{linkId:guid}")]
    public async Task<IActionResult> Revoke(
        Guid linkId, [FromBody] RevokeBody? body, CancellationToken ct)
    {
        await _mediator.Send(
            new RevokeDoctorPatientLinkCommand(linkId, body?.Reason), ct);
        return NoContent();
    }

    [Authorize(Roles = Roles.Doctor)]
    [HttpGet("my-patients")]
    public async Task<ActionResult<PagedResult<DoctorPatientLinkDto>>> MyPatients(
        [FromQuery] DoctorPatientStatus? status,
        [FromQuery] int page = 1, [FromQuery] int pageSize = 50,
        CancellationToken ct = default)
        => Ok(await _mediator.Send(
            new GetMyPatientsQuery(status, new PageRequest { Page = page, PageSize = pageSize }), ct));

    [HttpGet("my-doctors")]
    public async Task<ActionResult<PagedResult<DoctorPatientLinkDto>>> MyDoctors(
        [FromQuery] DoctorPatientStatus? status,
        [FromQuery] int page = 1, [FromQuery] int pageSize = 50,
        CancellationToken ct = default)
        => Ok(await _mediator.Send(
            new GetMyDoctorsQuery(status, new PageRequest { Page = page, PageSize = pageSize }), ct));
}

public record RespondBody(bool Accept, string? Note);
public record RevokeBody(string? Reason);


[ApiController]
[Route("api/users")]
[Authorize]
public class UsersController : ControllerBase
{
    private readonly IMediator _mediator;
    public UsersController(IMediator mediator) => _mediator = mediator;

    [HttpPatch("me")]
    public async Task<IActionResult> UpdateProfile(
        [FromBody] UpdateProfileCommand cmd, CancellationToken ct)
    {
        await _mediator.Send(cmd, ct);
        return NoContent();
    }

    [HttpPost("me/avatar")]
    public async Task<ActionResult<string>> UpdateAvatar(
        IFormFile file, CancellationToken ct)
    {
        if (file is null) return BadRequest(new { error = "File required" });

        await using var stream = file.OpenReadStream();
        var url = await _mediator.Send(
            new UpdateAvatarCommand(stream, file.FileName, file.ContentType), ct);
        return Ok(new { avatarUrl = url });
    }

    // NOTE: GET /my-doctors moved to DoctorsController (/api/doctors/my-doctors)
    // for consistency with /api/doctors/my-patients.
}


[ApiController]
[Route("api/notifications")]
[Authorize]
public class NotificationsController : ControllerBase
{
    private readonly IMediator _mediator;
    public NotificationsController(IMediator mediator) => _mediator = mediator;

    [HttpGet]
    public async Task<ActionResult<PagedResult<NotificationDto>>> GetMine(
        [FromQuery] bool? unreadOnly,
        [FromQuery] int page = 1, [FromQuery] int pageSize = 50,
        CancellationToken ct = default)
        => Ok(await _mediator.Send(
            new GetMyNotificationsQuery(unreadOnly, new PageRequest { Page = page, PageSize = pageSize }), ct));

    [HttpGet("unread-count")]
    public async Task<ActionResult<int>> UnreadCount(CancellationToken ct)
    {
        var count = await _mediator.Send(new GetUnreadCountQuery(), ct);
        return Ok(new { count });
    }

    [HttpPatch("{id:guid}/read")]
    public async Task<IActionResult> MarkRead(Guid id, CancellationToken ct)
    {
        await _mediator.Send(new MarkNotificationReadCommand(id), ct);
        return NoContent();
    }

    [HttpPost("mark-all-read")]
    public async Task<IActionResult> MarkAllRead(CancellationToken ct)
    {
        await _mediator.Send(new MarkAllNotificationsReadCommand(), ct);
        return NoContent();
    }
}


[ApiController]
[Route("api/admin")]
[Authorize(Roles = Roles.Administrator)]
public class AdminController : ControllerBase
{
    private readonly IMediator _mediator;
    public AdminController(IMediator mediator) => _mediator = mediator;

    [HttpGet("users")]
    public async Task<ActionResult<PagedResult<UserDto>>> ListUsers(
        [FromQuery] string? role,
        [FromQuery] string? search,
        [FromQuery] int page = 1, [FromQuery] int pageSize = 50,
        CancellationToken ct = default)
        => Ok(await _mediator.Send(
            new GetAllUsersQuery(role, search, new PageRequest { Page = page, PageSize = pageSize }), ct));

    [HttpPost("users/{id:guid}/ban")]
    public async Task<IActionResult> BanUser(
        Guid id, [FromBody] BanRequest body, CancellationToken ct)
    {
        await _mediator.Send(new SetUserBanStatusCommand(id, body.IsBanned, body.Reason), ct);
        return NoContent();
    }

    [HttpPost("users/{id:guid}/role")]
    public async Task<IActionResult> ChangeRole(
        Guid id, [FromBody] ChangeRoleRequest body, CancellationToken ct)
    {
        await _mediator.Send(new ChangeUserRoleCommand(id, body.NewRole), ct);
        return NoContent();
    }

    [HttpGet("audit-log")]
    public async Task<ActionResult<PagedResult<AuditLogDto>>> AuditLog(
        [FromQuery] Guid? userId,
        [FromQuery] AuditAction? action,
        [FromQuery] DateTimeOffset? from,
        [FromQuery] DateTimeOffset? to,
        [FromQuery] int page = 1, [FromQuery] int pageSize = 100,
        CancellationToken ct = default)
        => Ok(await _mediator.Send(
            new GetAuditLogQuery(userId, action, from, to,
                new PageRequest { Page = page, PageSize = pageSize }), ct));
}

public record BanRequest(bool IsBanned, string? Reason);
public record ChangeRoleRequest(string NewRole);
