using AutoMapper;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Application.Common.Models;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Notifications;

public class GetMyNotificationsHandler : IRequestHandler<GetMyNotificationsQuery, PagedResult<NotificationDto>>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IMapper _mapper;

    public GetMyNotificationsHandler(IHemaxDbContext db, ICurrentUserService current, IMapper mapper)
    {
        _db = db; _current = current; _mapper = mapper;
    }

    public async Task<PagedResult<NotificationDto>> Handle(
        GetMyNotificationsQuery q, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var query = _db.Notifications.Where(n => n.UserId == _current.UserId);
        if (q.UnreadOnly == true) query = query.Where(n => !n.IsRead);

        var total = await query.CountAsync(ct);
        var items = await query
            .OrderByDescending(n => n.CreatedAt)
            .Skip(q.Page.Skip).Take(q.Page.Take)
            .ToListAsync(ct);

        return new PagedResult<NotificationDto>
        {
            Items      = items.Select(n => _mapper.Map<NotificationDto>(n)).ToList().AsReadOnly(),
            Page       = q.Page.Page,
            PageSize   = q.Page.PageSize,
            TotalItems = total,
        };
    }
}

public class GetUnreadCountHandler : IRequestHandler<GetUnreadCountQuery, int>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;

    public GetUnreadCountHandler(IHemaxDbContext db, ICurrentUserService current)
    {
        _db = db; _current = current;
    }

    public async Task<int> Handle(GetUnreadCountQuery q, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();
        return await _db.Notifications
            .CountAsync(n => n.UserId == _current.UserId && !n.IsRead, ct);
    }
}

public class MarkNotificationReadHandler : IRequestHandler<MarkNotificationReadCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IDateTimeProvider _clock;

    public MarkNotificationReadHandler(IHemaxDbContext db, ICurrentUserService current, IDateTimeProvider clock)
    {
        _db = db; _current = current; _clock = clock;
    }

    public async Task Handle(MarkNotificationReadCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var n = await _db.Notifications.FirstOrDefaultAsync(
            x => x.Id == cmd.NotificationId && x.UserId == _current.UserId, ct)
            ?? throw new EntityNotFoundException("Notification", cmd.NotificationId);

        if (!n.IsRead)
        {
            n.IsRead = true;
            n.ReadAt = _clock.UtcNow;
            await _db.SaveChangesAsync(ct);
        }
    }
}

public class MarkAllNotificationsReadHandler : IRequestHandler<MarkAllNotificationsReadCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IDateTimeProvider _clock;

    public MarkAllNotificationsReadHandler(IHemaxDbContext db, ICurrentUserService current, IDateTimeProvider clock)
    {
        _db = db; _current = current; _clock = clock;
    }

    public async Task Handle(MarkAllNotificationsReadCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var unread = await _db.Notifications
            .Where(n => n.UserId == _current.UserId && !n.IsRead)
            .ToListAsync(ct);

        foreach (var n in unread)
        {
            n.IsRead = true;
            n.ReadAt = _clock.UtcNow;
        }
        await _db.SaveChangesAsync(ct);
    }
}
