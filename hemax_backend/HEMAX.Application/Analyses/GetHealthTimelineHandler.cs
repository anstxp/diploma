using System.Text.Json;
using HEMAX.Application.Common;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Analyses;

public class GetHealthTimelineHandler : IRequestHandler<GetHealthTimelineQuery, IReadOnlyList<TimelinePoint>>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;

    public GetHealthTimelineHandler(IHemaxDbContext db, ICurrentUserService current)
    {
        _db = db; _current = current;
    }

    public async Task<IReadOnlyList<TimelinePoint>> Handle(
        GetHealthTimelineQuery q, CancellationToken ct)
    {
        var userId = q.UserId ?? _current.UserId
            ?? throw new Common.Exceptions.UnauthorizedException();

        await AuthorizationGuard.EnsureCanViewUserDataAsync(_db, _current, userId, ct);

        var queryable = _db.Analyses.Where(a => a.UserId == userId && a.Type == q.Type);
        if (q.From.HasValue) queryable = queryable.Where(a => a.CreatedAt >= q.From);
        if (q.To.HasValue)   queryable = queryable.Where(a => a.CreatedAt <= q.To);

        var rows = await queryable
            .OrderBy(a => a.CreatedAt)
            .Select(a => new { a.Id, a.CreatedAt, a.ResultJson })
            .ToListAsync(ct);

        var points = new List<TimelinePoint>(rows.Count);
        foreach (var row in rows)
        {
            var (value, flag) = ExtractFieldValue(row.ResultJson, q.Type, q.Field);
            points.Add(new TimelinePoint(row.CreatedAt, value, flag, row.Id));
        }
        return points;
    }

    private static (double?, string?) ExtractFieldValue(string json, AnalysisType type, string field)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;

            if (root.TryGetProperty("labs", out var labs) && labs.ValueKind == JsonValueKind.Array)
            {
                foreach (var lab in labs.EnumerateArray())
                {
                    if (lab.TryGetProperty("code", out var code)
                        && string.Equals(code.GetString(), field, StringComparison.OrdinalIgnoreCase))
                    {
                        var v = lab.TryGetProperty("value", out var val) ? val.GetDouble() : (double?)null;
                        var f = lab.TryGetProperty("flag", out var flagEl) ? flagEl.GetString() : null;
                        return (v, f);
                    }
                }
            }

            if (root.TryGetProperty("risks", out var risks) && risks.ValueKind == JsonValueKind.Array)
            {
                foreach (var risk in risks.EnumerateArray())
                {
                    if (risk.TryGetProperty("target", out var target)
                        && string.Equals(target.GetString(), field, StringComparison.OrdinalIgnoreCase))
                    {
                        var p = risk.TryGetProperty("probability", out var prob) ? prob.GetDouble() : (double?)null;
                        var t = risk.TryGetProperty("risk_tier", out var tier) ? tier.GetString() : null;
                        return (p, t);
                    }
                }
            }

            if (type == AnalysisType.Derma
                && root.TryGetProperty("all_probabilities", out var probs)
                && probs.TryGetProperty(field, out var fieldProb))
            {
                return (fieldProb.GetDouble(), null);
            }
        }
        catch (JsonException) { /* fall through */ }

        return (null, null);
    }
}
