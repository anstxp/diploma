using AutoMapper;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Analyses;

/// <summary>
/// Lets a doctor attach a clinical note + "reviewed" timestamp to a patient's
/// analysis. Requires an accepted DoctorPatientLink (or admin role).
/// Notifies the patient.
/// </summary>
public class AnnotateAnalysisHandler : IRequestHandler<AnnotateAnalysisCommand, AnalysisDto>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IDateTimeProvider _clock;
    private readonly INotificationService _notify;
    private readonly IAuditService _audit;
    private readonly IMapper _mapper;

    public AnnotateAnalysisHandler(
        IHemaxDbContext db, ICurrentUserService current, IDateTimeProvider clock,
        INotificationService notify, IAuditService audit, IMapper mapper)
    {
        _db = db; _current = current; _clock = clock;
        _notify = notify; _audit = audit; _mapper = mapper;
    }

    public async Task<AnalysisDto> Handle(AnnotateAnalysisCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var a = await _db.Analyses.FirstOrDefaultAsync(x => x.Id == cmd.AnalysisId, ct)
            ?? throw new EntityNotFoundException("Analysis", cmd.AnalysisId);

        if (!_current.IsInRole(Roles.Administrator))
        {
            var hasLink = await _db.DoctorPatientLinks.AnyAsync(l =>
                l.DoctorId  == _current.UserId &&
                l.PatientId == a.UserId &&
                l.Status    == DoctorPatientStatus.Accepted, ct);
            if (!hasLink) throw new ForbiddenException("No accepted patient link.");
        }

        a.DoctorReviewedById = _current.UserId;
        a.DoctorReviewedAt   = _clock.UtcNow;
        a.DoctorNote         = cmd.Note;
        await _db.SaveChangesAsync(ct);

        await _notify.NotifyAsync(a.UserId, NotificationType.AnalysisAnnotated,
            "Лікар додав примітку до вашого аналізу",
            cmd.Note.Length > 200 ? cmd.Note.Substring(0, 200) + "..." : cmd.Note,
            link: $"/analyses/{a.Id}",
            relatedEntityId: a.Id, ct: ct);

        await _audit.LogAsync(AuditAction.AnalysisSubmitted, "Analysis", a.Id,
            new { action = "annotated" }, ct);

        return _mapper.Map<AnalysisDto>(a);
    }
}
