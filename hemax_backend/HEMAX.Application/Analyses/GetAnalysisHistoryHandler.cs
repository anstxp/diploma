using AutoMapper;
using HEMAX.Application.Common;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Application.Common.Models;
using HEMAX.Domain.Enums;
using HEMAX.Infrastructure.Files;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Analyses;

public class GetAnalysisHistoryHandler : IRequestHandler<GetAnalysisHistoryQuery, PagedResult<AnalysisDto>>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IMapper _mapper;
    private readonly IFileUrlGenerator _urls;

    public GetAnalysisHistoryHandler(
        IHemaxDbContext db, ICurrentUserService current, IMapper mapper,
        IFileUrlGenerator urls)
    {
        _db = db; _current = current; _mapper = mapper; _urls = urls;
    }

    public async Task<PagedResult<AnalysisDto>> Handle(
        GetAnalysisHistoryQuery query, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var targetUserId = query.UserId ?? _current.UserId.Value;

        await AuthorizationGuard.EnsureCanViewUserDataAsync(
            _db, _current, targetUserId, ct);

        var q = _db.Analyses.Where(a => a.UserId == targetUserId);

        if (query.Type.HasValue)        q = q.Where(a => a.Type == query.Type);
        if (query.MinSeverity.HasValue) q = q.Where(a => a.Severity >= query.MinSeverity);
        if (query.From.HasValue)        q = q.Where(a => a.CreatedAt >= query.From);
        if (query.To.HasValue)          q = q.Where(a => a.CreatedAt <= query.To);

        var total = await q.CountAsync(ct);
        var items = await q
            .OrderByDescending(a => a.CreatedAt)
            .Skip(query.Page.Skip).Take(query.Page.Take)
            .ToListAsync(ct);

        // Fetch file attachments in one query.
        var ids = items.Select(a => a.Id).ToList();
        var files = await _db.FileAssets
            .Where(f => f.RelatedEntityId.HasValue && ids.Contains(f.RelatedEntityId.Value)
                     && (f.Type == FileAssetType.LesionImage || f.Type == FileAssetType.PdfReport))
            .ToListAsync(ct);
        var fileByAnalysisId = files
            .GroupBy(f => f.RelatedEntityId!.Value)
            .ToDictionary(g => g.Key, g => g.OrderByDescending(f => f.CreatedAt).First());

        var dtos = items.Select(a =>
        {
            var dto = _mapper.Map<AnalysisDto>(a);
            if (fileByAnalysisId.TryGetValue(a.Id, out var f))
                return dto with { FileUrl = _urls.GetDownloadUrl(f.StorageKey), FileName = f.FileName };
            return dto;
        }).ToList().AsReadOnly();

        return new PagedResult<AnalysisDto>
        {
            Items      = dtos,
            Page       = query.Page.Page,
            PageSize   = query.Page.PageSize,
            TotalItems = total,
        };
    }
}
