using System.Text.Json;
using AutoMapper;
using HEMAX.Application.Common;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Exceptions;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Analyses;

public class CompareAnalysesHandler : IRequestHandler<CompareAnalysesQuery, AnalysisComparisonDto>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IMapper _mapper;

    public CompareAnalysesHandler(IHemaxDbContext db, ICurrentUserService current, IMapper mapper)
    {
        _db = db; _current = current; _mapper = mapper;
    }

    public async Task<AnalysisComparisonDto> Handle(CompareAnalysesQuery q, CancellationToken ct)
    {
        var older = await _db.Analyses.FirstOrDefaultAsync(a => a.Id == q.OlderId, ct)
            ?? throw new EntityNotFoundException("Analysis", q.OlderId);
        var newer = await _db.Analyses.FirstOrDefaultAsync(a => a.Id == q.NewerId, ct)
            ?? throw new EntityNotFoundException("Analysis", q.NewerId);

        if (older.UserId != newer.UserId)
            throw new BusinessRuleViolationException("DIFFERENT_USERS",
                "Both analyses must belong to the same user");

        if (older.Type != newer.Type)
            throw new BusinessRuleViolationException("DIFFERENT_TYPES",
                "Comparison requires same analysis type");

        await AuthorizationGuard.EnsureCanViewUserDataAsync(_db, _current, older.UserId, ct);

        var changes = ComputeChanges(older.ResultJson, newer.ResultJson);

        return new AnalysisComparisonDto(
            _mapper.Map<AnalysisDetailDto>(older),
            _mapper.Map<AnalysisDetailDto>(newer),
            changes);
    }

    private static Dictionary<string, ChangeIndicator> ComputeChanges(
        string olderJson, string newerJson)
    {
        var changes = new Dictionary<string, ChangeIndicator>();

        try
        {
            using var oldDoc = JsonDocument.Parse(olderJson);
            using var newDoc = JsonDocument.Parse(newerJson);

            var oldLabs = ExtractLabs(oldDoc.RootElement);
            var newLabs = ExtractLabs(newDoc.RootElement);

            foreach (var code in oldLabs.Keys.Union(newLabs.Keys))
            {
                var hasOld = oldLabs.TryGetValue(code, out var oldEntry);
                var hasNew = newLabs.TryGetValue(code, out var newEntry);

                var direction = (hasOld, hasNew) switch
                {
                    (false, true)  => "new",
                    (true, false)  => "missing",
                    (true, true) when oldEntry.flag == newEntry.flag                                       => "stable",
                    (true, true) when oldEntry.flag != "normal" && oldEntry.flag != null && newEntry.flag == "normal" => "improved",
                    (true, true) when oldEntry.flag == "normal" && newEntry.flag != null && newEntry.flag != "normal" => "worsened",
                    _ => "changed",
                };

                changes[code] = new ChangeIndicator(
                    OldValue:  hasOld ? oldEntry.value : null,
                    NewValue:  hasNew ? newEntry.value : null,
                    OldFlag:   hasOld ? oldEntry.flag  : null,
                    NewFlag:   hasNew ? newEntry.flag  : null,
                    Direction: direction);
            }
        }
        catch (JsonException) { /* return whatever we collected so far */ }

        return changes;
    }

    private static Dictionary<string, (double? value, string? flag)> ExtractLabs(JsonElement root)
    {
        var dict = new Dictionary<string, (double?, string?)>(StringComparer.OrdinalIgnoreCase);

        if (root.TryGetProperty("labs", out var labs) && labs.ValueKind == JsonValueKind.Array)
        {
            foreach (var lab in labs.EnumerateArray())
            {
                if (!lab.TryGetProperty("code", out var code)) continue;
                var c = code.GetString();
                if (string.IsNullOrEmpty(c)) continue;

                double? v = lab.TryGetProperty("value", out var val) && val.ValueKind == JsonValueKind.Number
                    ? val.GetDouble() : (double?)null;
                string? f = lab.TryGetProperty("flag", out var flagEl) && flagEl.ValueKind == JsonValueKind.String
                    ? flagEl.GetString() : null;

                dict[c] = (v, f);
            }
        }

        return dict;
    }
}
