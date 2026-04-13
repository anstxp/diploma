using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Common;
using HEMAX.Domain.Entities;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Infrastructure.Persistence;

public class HemaxDbContext
    : IdentityDbContext<ApplicationUser, ApplicationRole, Guid>, IHemaxDbContext
{
    private readonly ICurrentUserService? _currentUser;
    private readonly IDateTimeProvider? _clock;
    private readonly IEncryptionService? _encryption;

    public HemaxDbContext(DbContextOptions<HemaxDbContext> options) : base(options) { }

    public HemaxDbContext(
        DbContextOptions<HemaxDbContext> options,
        ICurrentUserService currentUser,
        IDateTimeProvider clock,
        IEncryptionService encryption) : base(options)
    {
        _currentUser = currentUser;
        _clock = clock;
        _encryption = encryption;
    }

    public DbSet<Analysis>           Analyses           => Set<Analysis>();
    public DbSet<BlogPost>           BlogPosts          => Set<BlogPost>();
    public DbSet<Comment>            Comments           => Set<Comment>();
    public DbSet<PostLike>           PostLikes          => Set<PostLike>();
    public DbSet<DoctorPatientLink>  DoctorPatientLinks => Set<DoctorPatientLink>();
    public DbSet<RefreshToken>       RefreshTokens      => Set<RefreshToken>();
    public DbSet<Notification>       Notifications      => Set<Notification>();
    public DbSet<AuditLog>           AuditLogs          => Set<AuditLog>();
    public DbSet<FileAsset>          FileAssets         => Set<FileAsset>();
    public DbSet<EmailVerification>  EmailVerifications => Set<EmailVerification>();
    public DbSet<UserProfile>        UserProfiles       => Set<UserProfile>();

    DbSet<ApplicationUser> IHemaxDbContext.Users => Users;

    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder);

        builder.ApplyConfigurationsFromAssembly(typeof(HemaxDbContext).Assembly);

        // Identity table renames (cleaner names)
        builder.Entity<ApplicationUser>(b => b.ToTable("Users"));
        builder.Entity<ApplicationRole>(b => b.ToTable("Roles"));
        builder.Entity<Microsoft.AspNetCore.Identity.IdentityUserRole<Guid>>(b => b.ToTable("UserRoles"));
        builder.Entity<Microsoft.AspNetCore.Identity.IdentityUserClaim<Guid>>(b => b.ToTable("UserClaims"));
        builder.Entity<Microsoft.AspNetCore.Identity.IdentityUserLogin<Guid>>(b => b.ToTable("UserLogins"));
        builder.Entity<Microsoft.AspNetCore.Identity.IdentityRoleClaim<Guid>>(b => b.ToTable("RoleClaims"));
        builder.Entity<Microsoft.AspNetCore.Identity.IdentityUserToken<Guid>>(b => b.ToTable("UserTokens"));

        builder.Entity<BlogPost>().HasQueryFilter(p => !p.IsDeleted);
        builder.Entity<Comment>().HasQueryFilter(c => !c.IsDeleted);

        // ────────────────────────────────────────────────────────────
        // PHI encryption — AES-256-GCM transparent column encryption
        //
        // CRITICAL: these columns contain Protected Health Information
        // (lab values, diagnoses, doctor's clinical notes). Encrypt at
        // rest per HIPAA §164.312(a)(2)(iv) / GDPR Art. 32(1)(a).
        //
        // The same encrypted value never appears twice (per-row nonce),
        // so equality search on these columns is impossible. That's by
        // design: PHI must never be in a WHERE clause anyway.
        // ────────────────────────────────────────────────────────────

        if (_encryption is not null)
        {
            var enc      = new EncryptedStringConverter(_encryption);
            var encNull  = new NullableEncryptedStringConverter(_encryption);

            builder.Entity<Analysis>().Property(a => a.RawInputJson)
                .HasConversion(enc).HasColumnType("nvarchar(max)");
            builder.Entity<Analysis>().Property(a => a.ResultJson)
                .HasConversion(enc).HasColumnType("nvarchar(max)");
            builder.Entity<Analysis>().Property(a => a.DoctorNote)
                .HasConversion(encNull).HasColumnType("nvarchar(max)");
            builder.Entity<Analysis>().Property(a => a.SummaryUa)
                .HasConversion(encNull).HasColumnType("nvarchar(max)");

            builder.Entity<Notification>().Property(n => n.Body)
                .HasConversion(enc).HasColumnType("nvarchar(max)");

            builder.Entity<DoctorPatientLink>().Property(l => l.InviteMessage)
                .HasConversion(encNull).HasColumnType("nvarchar(max)");
            builder.Entity<DoctorPatientLink>().Property(l => l.Note)
                .HasConversion(encNull).HasColumnType("nvarchar(max)");

            builder.Entity<AuditLog>().Property(a => a.DetailsJson)
                .HasConversion(encNull).HasColumnType("nvarchar(max)");

            builder.Entity<UserProfile>().Property(p => p.MiddleName).HasConversion(encNull);
            builder.Entity<UserProfile>().Property(p => p.Phone).HasConversion(encNull);
            builder.Entity<UserProfile>().Property(p => p.ChronicDiseases)
                .HasConversion(encNull).HasColumnType("nvarchar(max)");
            builder.Entity<UserProfile>().Property(p => p.Allergies)
                .HasConversion(encNull).HasColumnType("nvarchar(max)");
            builder.Entity<UserProfile>().Property(p => p.CurrentMedications)
                .HasConversion(encNull).HasColumnType("nvarchar(max)");
            builder.Entity<UserProfile>().Property(p => p.FamilyHistory)
                .HasConversion(encNull).HasColumnType("nvarchar(max)");
            builder.Entity<UserProfile>().Property(p => p.EmergencyContactName).HasConversion(encNull);
            builder.Entity<UserProfile>().Property(p => p.EmergencyContactPhone).HasConversion(encNull);
        }

        builder.Entity<UserProfile>(b =>
        {
            b.HasKey(p => p.Id);
            b.HasIndex(p => p.UserId).IsUnique();
            b.HasOne(p => p.User)
                .WithOne()
                .HasForeignKey<UserProfile>(p => p.UserId)
                .OnDelete(DeleteBehavior.Cascade);
            b.Ignore(p => p.Bmi);  // computed property only

            b.Property(p => p.PhoneHash).HasMaxLength(64);
            b.HasIndex(p => p.PhoneHash)
                .IsUnique()
                .HasFilter("[PhoneHash] IS NOT NULL")
                .HasDatabaseName("IX_UserProfiles_PhoneHash_Unique");
        });
    }

    public override async Task<int> SaveChangesAsync(CancellationToken ct = default)
    {
        var now = _clock?.UtcNow ?? DateTimeOffset.UtcNow;

        foreach (var entry in ChangeTracker.Entries<AuditableEntity>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    entry.Entity.CreatedAt = now;
                    break;
                case EntityState.Modified:
                    entry.Entity.UpdatedAt = now;
                    break;
            }
        }

        return await base.SaveChangesAsync(ct);
    }
}
