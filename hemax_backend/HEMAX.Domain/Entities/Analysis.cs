using HEMAX.Domain.Common;
using HEMAX.Domain.Enums;

namespace HEMAX.Domain.Entities;

public class Analysis : AuditableEntity
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid UserId { get; set; }
    public ApplicationUser? User { get; set; }

    public AnalysisType Type { get; set; }

    [Encrypted]
    public string RawInputJson { get; set; } = "{}";

    [Encrypted]
    public string ResultJson { get; set; } = "{}";

    public string? TopFlag { get; set; }

    public AnalysisSeverity Severity { get; set; } = AnalysisSeverity.Unknown;

    [Encrypted]
    public string? SummaryUa { get; set; }

    public string? Language { get; set; }

    public Guid? DoctorReviewedById { get; set; }
    public ApplicationUser? DoctorReviewedBy { get; set; }

    public DateTimeOffset? DoctorReviewedAt { get; set; }

    /// <summary>Free-text note from doctor.
    /// <b>Encrypted at rest</b> — physician-authored medical assessment (PHI).</summary>
    [Encrypted]
    public string? DoctorNote { get; set; }
}
