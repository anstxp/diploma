using HEMAX.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace HEMAX.Infrastructure.Persistence.Configurations;

public class ApplicationUserConfiguration : IEntityTypeConfiguration<ApplicationUser>
{
    public void Configure(EntityTypeBuilder<ApplicationUser> b)
    {
        b.Property(u => u.FirstName).IsRequired().HasMaxLength(100);
        b.Property(u => u.LastName).IsRequired().HasMaxLength(100);
        b.Property(u => u.AvatarUrl).HasMaxLength(500);
        b.Property(u => u.BanReason).HasMaxLength(500);
        b.Property(u => u.Sex).HasConversion<int>();

        b.HasIndex(u => u.Email).IsUnique();
    }
}

public class AnalysisConfiguration : IEntityTypeConfiguration<Analysis>
{
    public void Configure(EntityTypeBuilder<Analysis> b)
    {
        b.HasKey(a => a.Id);

        b.Property(a => a.Type).HasConversion<int>();
        b.Property(a => a.Severity).HasConversion<int>();
        b.Property(a => a.TopFlag).HasMaxLength(100);
        b.Property(a => a.Language).HasMaxLength(10);
        b.Property(a => a.RawInputJson).IsRequired();
        b.Property(a => a.ResultJson).IsRequired();

        b.HasOne(a => a.User)
            .WithMany(u => u.Analyses)
            .HasForeignKey(a => a.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        b.HasOne(a => a.DoctorReviewedBy)
            .WithMany()
            .HasForeignKey(a => a.DoctorReviewedById)
            .OnDelete(DeleteBehavior.SetNull);

        // Indexes for common queries
        b.HasIndex(a => new { a.UserId, a.CreatedAt });
        b.HasIndex(a => new { a.UserId, a.Type, a.CreatedAt });
        b.HasIndex(a => a.Severity);
    }
}

public class BlogPostConfiguration : IEntityTypeConfiguration<BlogPost>
{
    public void Configure(EntityTypeBuilder<BlogPost> b)
    {
        b.HasKey(p => p.Id);

        b.Property(p => p.Title).IsRequired().HasMaxLength(200);
        b.Property(p => p.Content).IsRequired().HasColumnType("nvarchar(max)");
        b.Property(p => p.Tags).HasMaxLength(500);
        b.Property(p => p.CoverImageStorageKey).HasMaxLength(500);
        b.Property(p => p.CoverImageFileName).HasMaxLength(255);

        b.HasOne(p => p.Author)
            .WithMany(u => u.BlogPosts)
            .HasForeignKey(p => p.AuthorId)
            .OnDelete(DeleteBehavior.Cascade);

        b.HasIndex(p => new { p.IsDeleted, p.IsPublished, p.CreatedAt });
        b.HasIndex(p => p.AuthorId);
    }
}

public class CommentConfiguration : IEntityTypeConfiguration<Comment>
{
    public void Configure(EntityTypeBuilder<Comment> b)
    {
        b.HasKey(c => c.Id);

        b.Property(c => c.Content).IsRequired().HasMaxLength(2000);

        b.HasOne(c => c.Post)
            .WithMany(p => p.Comments)
            .HasForeignKey(c => c.PostId)
            .OnDelete(DeleteBehavior.Cascade);

        b.HasOne(c => c.Author)
            .WithMany(u => u.Comments)
            .HasForeignKey(c => c.AuthorId)
            .OnDelete(DeleteBehavior.Restrict);

        b.HasIndex(c => new { c.PostId, c.CreatedAt });
    }
}

public class PostLikeConfiguration : IEntityTypeConfiguration<PostLike>
{
    public void Configure(EntityTypeBuilder<PostLike> b)
    {
        b.HasKey(l => l.Id);

        b.HasOne(l => l.Post)
            .WithMany(p => p.Likes)
            .HasForeignKey(l => l.PostId)
            .OnDelete(DeleteBehavior.Cascade);

        b.HasOne(l => l.User)
            .WithMany()
            .HasForeignKey(l => l.UserId)
            .OnDelete(DeleteBehavior.Restrict);

        // One like per (post, user)
        b.HasIndex(l => new { l.PostId, l.UserId }).IsUnique();
    }
}

public class DoctorPatientLinkConfiguration : IEntityTypeConfiguration<DoctorPatientLink>
{
    public void Configure(EntityTypeBuilder<DoctorPatientLink> b)
    {
        b.HasKey(l => l.Id);

        b.Property(l => l.Status).HasConversion<int>();
        // InviteMessage and Note encrypted in DbContext (nvarchar(max))

        b.HasOne(l => l.Doctor)
            .WithMany(u => u.AsDoctorRelations)
            .HasForeignKey(l => l.DoctorId)
            .OnDelete(DeleteBehavior.Restrict);

        b.HasOne(l => l.Patient)
            .WithMany(u => u.AsPatientRelations)
            .HasForeignKey(l => l.PatientId)
            .OnDelete(DeleteBehavior.Restrict);

        b.HasIndex(l => new { l.DoctorId, l.PatientId, l.Status });
    }
}

public class RefreshTokenConfiguration : IEntityTypeConfiguration<RefreshToken>
{
    public void Configure(EntityTypeBuilder<RefreshToken> b)
    {
        b.HasKey(t => t.Id);

        b.Property(t => t.TokenHash).IsRequired().HasMaxLength(128);
        b.Property(t => t.ReplacedByTokenHash).HasMaxLength(128);
        b.Property(t => t.CreatedByIp).HasMaxLength(45);
        b.Property(t => t.UserAgent).HasMaxLength(500);

        b.HasOne(t => t.User)
            .WithMany(u => u.RefreshTokens)
            .HasForeignKey(t => t.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        b.HasIndex(t => t.TokenHash).IsUnique();
        b.HasIndex(t => t.UserId);
    }
}

public class NotificationConfiguration : IEntityTypeConfiguration<Notification>
{
    public void Configure(EntityTypeBuilder<Notification> b)
    {
        b.HasKey(n => n.Id);

        b.Property(n => n.Type).HasConversion<int>();
        b.Property(n => n.Title).IsRequired().HasMaxLength(200);
        b.Property(n => n.Body).IsRequired();
        b.Property(n => n.Link).HasMaxLength(500);

        b.HasOne(n => n.User)
            .WithMany(u => u.Notifications)
            .HasForeignKey(n => n.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        b.HasIndex(n => new { n.UserId, n.IsRead, n.CreatedAt });
    }
}

public class AuditLogConfiguration : IEntityTypeConfiguration<AuditLog>
{
    public void Configure(EntityTypeBuilder<AuditLog> b)
    {
        b.HasKey(a => a.Id);

        b.Property(a => a.Action).HasConversion<int>();
        b.Property(a => a.EntityType).HasMaxLength(100);
        b.Property(a => a.IpAddress).HasMaxLength(45);
        b.Property(a => a.UserAgent).HasMaxLength(500);
        b.Property(a => a.DetailsJson).HasColumnType("nvarchar(max)");

        b.HasOne(a => a.User)
            .WithMany()
            .HasForeignKey(a => a.UserId)
            .OnDelete(DeleteBehavior.SetNull);

        b.HasIndex(a => a.CreatedAt);
        b.HasIndex(a => new { a.UserId, a.Action });
    }
}

public class FileAssetConfiguration : IEntityTypeConfiguration<FileAsset>
{
    public void Configure(EntityTypeBuilder<FileAsset> b)
    {
        b.HasKey(f => f.Id);

        b.Property(f => f.Type).HasConversion<int>();
        b.Property(f => f.FileName).IsRequired().HasMaxLength(256);
        b.Property(f => f.ContentType).IsRequired().HasMaxLength(100);
        b.Property(f => f.StorageKey).IsRequired().HasMaxLength(500);
        b.Property(f => f.PublicUrl).HasMaxLength(1000);

        b.HasOne(f => f.Owner)
            .WithMany()
            .HasForeignKey(f => f.OwnerId)
            .OnDelete(DeleteBehavior.Cascade);

        b.HasIndex(f => f.OwnerId);
    }
}

public class EmailVerificationConfiguration : IEntityTypeConfiguration<EmailVerification>
{
    public void Configure(EntityTypeBuilder<EmailVerification> b)
    {
        b.HasKey(e => e.Id);

        b.Property(e => e.TokenHash).IsRequired().HasMaxLength(128);

        b.HasOne(e => e.User)
            .WithMany()
            .HasForeignKey(e => e.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        b.HasIndex(e => new { e.UserId, e.TokenHash }).IsUnique();
    }
}
