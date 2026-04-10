using AutoMapper;
using HEMAX.Application.Auth;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Application.Common.Models;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;

namespace HEMAX.Application.DoctorPatient;

public class InvitePatientHandler : IRequestHandler<InvitePatientCommand, Guid>
{
    private readonly IHemaxDbContext _db;
    private readonly IIdentityService _identity;
    private readonly ICurrentUserService _current;
    private readonly INotificationService _notify;
    private readonly IEmailService _email;
    private readonly IAuditService _audit;
    private readonly IConfiguration _config;

    public InvitePatientHandler(IHemaxDbContext db, IIdentityService identity,
        ICurrentUserService current, INotificationService notify,
        IEmailService email, IAuditService audit, IConfiguration config)
    {
        _db = db; _identity = identity; _current = current;
        _notify = notify; _email = email; _audit = audit; _config = config;
    }

    public async Task<Guid> Handle(InvitePatientCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var patient = await _identity.GetUserByEmailAsync(cmd.PatientEmail, ct)
            ?? throw new BusinessRuleViolationException("PATIENT_NOT_FOUND",
                "Користувача з таким email не знайдено. Запросіть пацієнта зареєструватись.");

        if (patient.Id == _current.UserId)
            throw new BusinessRuleViolationException("SELF_INVITE",
                "Не можна запросити самого себе.");

        // Check existing relationship
        var existing = await _db.DoctorPatientLinks.FirstOrDefaultAsync(l =>
            l.DoctorId == _current.UserId && l.PatientId == patient.Id &&
            (l.Status == DoctorPatientStatus.Pending || l.Status == DoctorPatientStatus.Accepted),
            ct);

        if (existing is not null)
            throw new DuplicateEntityException(
                "Активне запрошення/звязок вже існує");

        var doctor = await _identity.GetUserByIdAsync(_current.UserId.Value, ct)!;
        var link = new DoctorPatientLink
        {
            DoctorId       = _current.UserId.Value,
            PatientId      = patient.Id,
            Status         = DoctorPatientStatus.Pending,
            InviteMessage  = cmd.InviteMessage,
        };
        _db.DoctorPatientLinks.Add(link);
        await _db.SaveChangesAsync(ct);

        // Notify patient in-app
        var doctorName = doctor?.FullName ?? "Лікар";
        await _notify.NotifyAsync(patient.Id,
            NotificationType.DoctorRequest,
            $"Лікар {doctorName} хоче додати вас як пацієнта",
            cmd.InviteMessage ?? "Натисніть, щоб переглянути та відповісти.",
            link: $"/doctors/invites/{link.Id}",
            relatedEntityId: link.Id, ct: ct);

        // Email
        try
        {
            // Bug fix May 2026: link the patient to the SPA, not to the API.
            //
            // Previous URL was `{App:BaseUrl}/doctor-requests/{link.Id}`,
            // which had two problems:
            //   1. App:BaseUrl is the backend origin (https://localhost:5001),
            //      so the email link landed on the API server which has no
            //      HTML page for that path → 404.
            //   2. The path `/doctor-requests/{id}` doesn't exist in the
            //      frontend router; the actual route is
            //      `/doctors/invites/:linkId` (see src/router/index.js).
            //
            // We now read App:FrontendBaseUrl (a new config key) and use
            // the canonical SPA path. If FrontendBaseUrl is unset, we fall
            // back to App:BaseUrl with a logged warning — which preserves
            // legacy behaviour for any local dev environments that haven't
            // updated their config yet.
            var frontendBaseUrl = _config["App:FrontendBaseUrl"];
            if (string.IsNullOrWhiteSpace(frontendBaseUrl))
            {
                frontendBaseUrl = _config["App:BaseUrl"] ?? "";
            }
            frontendBaseUrl = frontendBaseUrl.TrimEnd('/');

            await _email.SendDoctorInviteAsync(
                patient.Email!, doctorName,
                $"{frontendBaseUrl}/doctors/invites/{link.Id}", ct);
        }
        catch { /* non-blocking */ }

        await _audit.LogAsync(AuditAction.DoctorRequestSent, "DoctorPatientLink", link.Id,
            new { patientEmail = cmd.PatientEmail }, ct);

        return link.Id;
    }
}

public class RespondToDoctorRequestHandler : IRequestHandler<RespondToDoctorRequestCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IDateTimeProvider _clock;
    private readonly INotificationService _notify;
    private readonly IAuditService _audit;

    public RespondToDoctorRequestHandler(IHemaxDbContext db, ICurrentUserService current,
        IDateTimeProvider clock, INotificationService notify, IAuditService audit)
    {
        _db = db; _current = current; _clock = clock;
        _notify = notify; _audit = audit;
    }

    public async Task Handle(RespondToDoctorRequestCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var link = await _db.DoctorPatientLinks
            .Include(l => l.Patient)
            .FirstOrDefaultAsync(l => l.Id == cmd.LinkId, ct)
            ?? throw new EntityNotFoundException("DoctorPatientLink", cmd.LinkId);

        if (link.PatientId != _current.UserId)
            throw new ForbiddenException("Only the invited patient can respond");

        if (link.Status != DoctorPatientStatus.Pending)
            throw new BusinessRuleViolationException("ALREADY_RESPONDED",
                $"Request already {link.Status}");

        link.Status      = cmd.Accept ? DoctorPatientStatus.Accepted : DoctorPatientStatus.Rejected;
        link.RespondedAt = _clock.UtcNow;
        link.Note        = cmd.Note;
        await _db.SaveChangesAsync(ct);

        // Notify doctor
        var patientName = link.Patient?.FullName ?? "Пацієнт";
        if (cmd.Accept)
        {
            await _notify.NotifyAsync(link.DoctorId,
                NotificationType.DoctorRequestAccepted,
                $"Пацієнт {patientName} прийняв ваш запит",
                "Ви можете переглядати їхні аналізи та додавати примітки.",
                link: $"/doctors/patients/{link.PatientId}",
                relatedEntityId: link.Id, ct: ct);
        }

        await _audit.LogAsync(AuditAction.DoctorRequestResponded, "DoctorPatientLink", link.Id,
            new { accept = cmd.Accept }, ct);
    }
}

public class RevokeDoctorPatientLinkHandler : IRequestHandler<RevokeDoctorPatientLinkCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IDateTimeProvider _clock;

    public RevokeDoctorPatientLinkHandler(IHemaxDbContext db, ICurrentUserService current, IDateTimeProvider clock)
    {
        _db = db; _current = current; _clock = clock;
    }

    public async Task Handle(RevokeDoctorPatientLinkCommand cmd, CancellationToken ct)
    {
        var link = await _db.DoctorPatientLinks.FirstOrDefaultAsync(l => l.Id == cmd.LinkId, ct)
            ?? throw new EntityNotFoundException("DoctorPatientLink", cmd.LinkId);

        if (link.DoctorId != _current.UserId && link.PatientId != _current.UserId)
            throw new ForbiddenException();

        link.Status      = DoctorPatientStatus.Revoked;
        link.RespondedAt = _clock.UtcNow;
        link.Note        = cmd.Reason;
        await _db.SaveChangesAsync(ct);
    }
}

public class GetMyPatientsHandler : IRequestHandler<GetMyPatientsQuery, PagedResult<DoctorPatientLinkDto>>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IMapper _mapper;

    public GetMyPatientsHandler(IHemaxDbContext db, ICurrentUserService current, IMapper mapper)
    {
        _db = db; _current = current; _mapper = mapper;
    }

    public async Task<PagedResult<DoctorPatientLinkDto>> Handle(
        GetMyPatientsQuery q, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var query = _db.DoctorPatientLinks
            .Include(l => l.Doctor).Include(l => l.Patient)
            .Where(l => l.DoctorId == _current.UserId);

        if (q.Status.HasValue)
            query = query.Where(l => l.Status == q.Status);

        var total = await query.CountAsync(ct);
        var items = await query
            .OrderByDescending(l => l.CreatedAt)
            .Skip(q.Page.Skip).Take(q.Page.Take)
            .ToListAsync(ct);

        return new PagedResult<DoctorPatientLinkDto>
        {
            Items      = items.Select(l => _mapper.Map<DoctorPatientLinkDto>(l)).ToList().AsReadOnly(),
            Page       = q.Page.Page,
            PageSize   = q.Page.PageSize,
            TotalItems = total,
        };
    }
}

public class GetMyDoctorsHandler : IRequestHandler<GetMyDoctorsQuery, PagedResult<DoctorPatientLinkDto>>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IMapper _mapper;

    public GetMyDoctorsHandler(IHemaxDbContext db, ICurrentUserService current, IMapper mapper)
    {
        _db = db; _current = current; _mapper = mapper;
    }

    public async Task<PagedResult<DoctorPatientLinkDto>> Handle(
        GetMyDoctorsQuery q, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var query = _db.DoctorPatientLinks
            .Include(l => l.Doctor).Include(l => l.Patient)
            .Where(l => l.PatientId == _current.UserId);

        if (q.Status.HasValue)
            query = query.Where(l => l.Status == q.Status);

        var total = await query.CountAsync(ct);
        var items = await query
            .OrderByDescending(l => l.CreatedAt)
            .Skip(q.Page.Skip).Take(q.Page.Take)
            .ToListAsync(ct);

        return new PagedResult<DoctorPatientLinkDto>
        {
            Items      = items.Select(l => _mapper.Map<DoctorPatientLinkDto>(l)).ToList().AsReadOnly(),
            Page       = q.Page.Page,
            PageSize   = q.Page.PageSize,
            TotalItems = total,
        };
    }
}
