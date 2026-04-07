using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Analyses;

public class DeleteAnalysisHandler : IRequestHandler<DeleteAnalysisCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;

    public DeleteAnalysisHandler(IHemaxDbContext db, ICurrentUserService current)
    {
        _db = db; _current = current;
    }

    public async Task Handle(DeleteAnalysisCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var a = await _db.Analyses.FirstOrDefaultAsync(x => x.Id == cmd.AnalysisId, ct)
            ?? throw new EntityNotFoundException("Analysis", cmd.AnalysisId);

        if (a.UserId != _current.UserId && !_current.IsInRole(Roles.Administrator))
            throw new ForbiddenException();

        _db.Analyses.Remove(a);
        await _db.SaveChangesAsync(ct);
    }
}
