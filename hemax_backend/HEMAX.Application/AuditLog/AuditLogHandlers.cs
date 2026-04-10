using AutoMapper;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Application.Common.Models;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.AuditLog;

public class GetAuditLogHandler : IRequestHandler<GetAuditLogQuery, PagedResult<AuditLogDto>>
{
    private readonly IHemaxDbContext _db;
    private readonly IMapper _mapper;

    public GetAuditLogHandler(IHemaxDbContext db, IMapper mapper)
    {
        _db = db; _mapper = mapper;
    }

    public async Task<PagedResult<AuditLogDto>> Handle(GetAuditLogQuery q, CancellationToken ct)
    {
        var query = _db.AuditLogs.Include(a => a.User).AsQueryable();

        if (q.UserId.HasValue) query = query.Where(a => a.UserId == q.UserId);
        if (q.Action.HasValue) query = query.Where(a => a.Action == q.Action);
        if (q.From.HasValue)   query = query.Where(a => a.CreatedAt >= q.From);
        if (q.To.HasValue)     query = query.Where(a => a.CreatedAt <= q.To);

        var total = await query.CountAsync(ct);
        var items = await query
            .OrderByDescending(a => a.CreatedAt)
            .Skip(q.Page.Skip).Take(q.Page.Take)
            .ToListAsync(ct);

        return new PagedResult<AuditLogDto>
        {
            Items      = items.Select(a => _mapper.Map<AuditLogDto>(a)).ToList().AsReadOnly(),
            Page       = q.Page.Page,
            PageSize   = q.Page.PageSize,
            TotalItems = total,
        };
    }
}
