using HEMAX.Domain.Common;
using HEMAX.Domain.Enums;

namespace HEMAX.Domain.Entities;

public class DoctorPatientLink : AuditableEntity
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid DoctorId { get; set; }
    public ApplicationUser? Doctor { get; set; }

    public Guid PatientId { get; set; }
    public ApplicationUser? Patient { get; set; }

    public DoctorPatientStatus Status { get; set; } = DoctorPatientStatus.Pending;

    public DateTimeOffset? RespondedAt { get; set; }

    [Encrypted]
    public string? InviteMessage { get; set; }

    [Encrypted]
    public string? Note { get; set; }
}
