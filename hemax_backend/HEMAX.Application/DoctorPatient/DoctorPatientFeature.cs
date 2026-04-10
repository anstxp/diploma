using HEMAX.Application.Common.Models;
using HEMAX.Domain.Enums;
using FluentValidation;
using MediatR;

namespace HEMAX.Application.DoctorPatient;


public record DoctorPatientLinkDto(
    Guid Id,
    Guid DoctorId,
    string DoctorName,
    string DoctorEmail,
    string? DoctorAvatarUrl,
    Guid PatientId,
    string PatientName,
    string PatientEmail,
    string? PatientAvatarUrl,
    int? PatientAge,
    DoctorPatientStatus Status,
    DateTimeOffset CreatedAt,
    DateTimeOffset? RespondedAt,
    string? InviteMessage,
    string? Note
);

public record InvitePatientCommand(
    string PatientEmail,
    string? InviteMessage
) : IRequest<Guid>;

public record RespondToDoctorRequestCommand(
    Guid LinkId,
    bool Accept,
    string? Note
) : IRequest;

public record RevokeDoctorPatientLinkCommand(
    Guid LinkId,
    string? Reason
) : IRequest;

public record GetMyPatientsQuery(
    DoctorPatientStatus? Status,
    PageRequest Page
) : IRequest<PagedResult<DoctorPatientLinkDto>>;

public record GetMyDoctorsQuery(
    DoctorPatientStatus? Status,
    PageRequest Page
) : IRequest<PagedResult<DoctorPatientLinkDto>>;


public class InvitePatientCommandValidator : AbstractValidator<InvitePatientCommand>
{
    public InvitePatientCommandValidator()
    {
        RuleFor(x => x.PatientEmail).NotEmpty().EmailAddress();
        RuleFor(x => x.InviteMessage).MaximumLength(500);
    }
}

public class RespondToDoctorRequestCommandValidator : AbstractValidator<RespondToDoctorRequestCommand>
{
    public RespondToDoctorRequestCommandValidator()
    {
        RuleFor(x => x.LinkId).NotEmpty();
        RuleFor(x => x.Note).MaximumLength(500);
    }
}
