namespace HEMAX.Domain.Enums;

public static class Roles
{
    public const string Administrator = "Administrator";
    public const string Doctor        = "Doctor";
    public const string User          = "User";

    public static readonly IReadOnlyList<string> All = new[]
    {
        Administrator, Doctor, User,
    };
}

public enum AnalysisType
{
    Cbc   = 1,
    Chem  = 2,
    Risk  = 3,
    Neuro = 4,
    Derma = 5,
}

public enum AnalysisSeverity
{
    Unknown  = 0,
    Low      = 1,
    Moderate = 2,
    High     = 3,
    Critical = 4,
}

public enum DoctorPatientStatus
{
    Pending  = 0,
    Accepted = 1,
    Rejected = 2,
    Revoked  = 3,
}

public enum NotificationType
{
    NewBlogPost          = 1,
    NewComment           = 2,
    DoctorRequest        = 3,
    DoctorRequestAccepted = 4,
    AnalysisAnnotated    = 5,
    SystemAnnouncement   = 6,
}

public enum FileAssetType
{
    Avatar         = 1,
    LesionImage    = 2,
    PdfReport      = 3,
    BlogAttachment = 4,
}

public enum AuditAction
{
    Login              = 1,
    Logout             = 2,
    Register           = 3,
    PasswordChanged    = 4,
    RoleChanged        = 5,
    AnalysisSubmitted  = 6,
    BlogPostCreated    = 7,
    BlogPostUpdated    = 8,
    BlogPostDeleted    = 9,
    CommentDeleted     = 10,
    DoctorRequestSent  = 11,
    DoctorRequestResponded = 12,
    UserBanned         = 13,
    UserProfileUpdated = 14,
}

public enum Sex
{
    Unknown = 0,
    Male    = 1,
    Female  = 2,
}

public enum AlcoholFrequency
{
    Unknown    = 0,
    Never      = 1,
    Occasional = 2,  // a few times a month or less
    Regular    = 3,  // weekly
    Heavy      = 4,  // multiple times per week
}

public enum PhysicalActivity
{
    Unknown   = 0,
    Sedentary = 1,  // mostly sitting, little exercise
    Light     = 2,  // walking, casual exercise 1-2/week
    Moderate  = 3,  // exercise 3-5/week
    Active    = 4,  // daily intense exercise or physical job
}

public enum DietType
{
    Unknown    = 0,
    Omnivore   = 1,
    Vegetarian = 2,
    Vegan      = 3,
    Keto       = 4,
    Other      = 5,
}
