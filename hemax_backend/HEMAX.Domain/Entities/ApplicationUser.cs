using HEMAX.Domain.Enums;
using Microsoft.AspNetCore.Identity;

namespace HEMAX.Domain.Entities;

public class ApplicationUser : IdentityUser<Guid>
{
    public string FirstName { get; set; } = string.Empty;
    public string LastName  { get; set; } = string.Empty;

    public DateOnly? DateOfBirth { get; set; }
    public Sex Sex { get; set; } = Sex.Unknown;

    public string? AvatarUrl { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset? UpdatedAt { get; set; }

    public bool IsBanned { get; set; }
    public string? BanReason { get; set; }

    // ─── Navigation ───
    public ICollection<Analysis>      Analyses           { get; set; } = new List<Analysis>();
    public ICollection<BlogPost>      BlogPosts          { get; set; } = new List<BlogPost>();
    public ICollection<Comment>       Comments           { get; set; } = new List<Comment>();
    public ICollection<RefreshToken>  RefreshTokens      { get; set; } = new List<RefreshToken>();
    public ICollection<Notification>  Notifications      { get; set; } = new List<Notification>();

    // Doctor-Patient
    public ICollection<DoctorPatientLink> AsDoctorRelations  { get; set; } = new List<DoctorPatientLink>();
    public ICollection<DoctorPatientLink> AsPatientRelations { get; set; } = new List<DoctorPatientLink>();

    public int? GetAge(DateOnly? today = null)
    {
        if (DateOfBirth is null) return null;
        var t = today ?? DateOnly.FromDateTime(DateTime.UtcNow);
        var age = t.Year - DateOfBirth.Value.Year;
        if (DateOfBirth.Value > t.AddYears(-age)) age--;
        return age;
    }

    public string FullName => $"{FirstName} {LastName}".Trim();
}

public class ApplicationRole : IdentityRole<Guid>
{
    public string? Description { get; set; }

    public ApplicationRole() { }
    public ApplicationRole(string name) : base(name) { }
}
