using AutoMapper;
using HEMAX.Application.Analyses;
using HEMAX.Application.Auth;
using HEMAX.Application.BlogPosts;
using HEMAX.Application.DoctorPatient;
using HEMAX.Application.Notifications;
using HEMAX.Application.AuditLog;
using HEMAX.Domain.Entities;

namespace HEMAX.Application.Common.Mappings;

public class ApplicationMappingProfile : AutoMapper.Profile
{
    public ApplicationMappingProfile()
    {
        // ── User ──
        CreateMap<ApplicationUser, UserDto>()
            .ForCtorParam(nameof(UserDto.Roles), opt => opt.MapFrom(_ => Array.Empty<string>()));
        // Note: roles must be filled by caller (handler) since they're not on entity.

        // ── Analysis ──
        // FileUrl/FileName default to null; handlers populate them after fetching FileAsset.
        CreateMap<Analysis, AnalysisDto>()
            .ForCtorParam(nameof(AnalysisDto.FileUrl),  opt => opt.MapFrom((src, dest) => (string?)null))
            .ForCtorParam(nameof(AnalysisDto.FileName), opt => opt.MapFrom((src, dest) => (string?)null));
        CreateMap<Analysis, AnalysisDetailDto>()
            .ForCtorParam(nameof(AnalysisDetailDto.FileUrl),  opt => opt.MapFrom((src, dest) => (string?)null))
            .ForCtorParam(nameof(AnalysisDetailDto.FileName), opt => opt.MapFrom((src, dest) => (string?)null));

        // ── BlogPost ──
        CreateMap<BlogPost, BlogPostDto>()
            .ForCtorParam(nameof(BlogPostDto.AuthorName),
                opt => opt.MapFrom(p => p.Author == null ? "" : p.Author.FullName))
            .ForCtorParam(nameof(BlogPostDto.AuthorAvatarUrl),
                opt => opt.MapFrom(p => p.Author == null ? null : p.Author.AvatarUrl))
            .ForCtorParam(nameof(BlogPostDto.Tags),
                opt => opt.MapFrom(p => p.GetTagsList().ToList().AsReadOnly()))
            .ForCtorParam(nameof(BlogPostDto.CoverImageUrl),
                opt => opt.MapFrom((src, dest) => (string?)null))  // filled by handler
            .ForCtorParam(nameof(BlogPostDto.IsLikedByMe),
                opt => opt.MapFrom(_ => false));  // filled by handler

        CreateMap<BlogPost, BlogPostListItemDto>()
            .ForCtorParam(nameof(BlogPostListItemDto.AuthorName),
                opt => opt.MapFrom(p => p.Author == null ? "" : p.Author.FullName))
            .ForCtorParam(nameof(BlogPostListItemDto.AuthorAvatarUrl),
                opt => opt.MapFrom(p => p.Author == null ? null : p.Author.AvatarUrl))
            .ForCtorParam(nameof(BlogPostListItemDto.Tags),
                opt => opt.MapFrom(p => p.GetTagsList().ToList().AsReadOnly()))
            .ForCtorParam(nameof(BlogPostListItemDto.CoverImageUrl),
                opt => opt.MapFrom((src, dest) => (string?)null))  // filled by handler
            .ForCtorParam(nameof(BlogPostListItemDto.ContentPreview),
                opt => opt.MapFrom(p => Truncate(p.Content, 200)));

        // ── Comment ──
        CreateMap<Comment, CommentDto>()
            .ForCtorParam(nameof(CommentDto.AuthorName),
                opt => opt.MapFrom(c => c.Author == null ? "" : c.Author.FullName))
            .ForCtorParam(nameof(CommentDto.AuthorAvatarUrl),
                opt => opt.MapFrom(c => c.Author == null ? null : c.Author.AvatarUrl));

        // ── DoctorPatientLink ──
        CreateMap<DoctorPatientLink, DoctorPatientLinkDto>()
            .ForCtorParam(nameof(DoctorPatientLinkDto.DoctorName),
                opt => opt.MapFrom(l => l.Doctor == null ? "" : l.Doctor.FullName))
            .ForCtorParam(nameof(DoctorPatientLinkDto.DoctorEmail),
                opt => opt.MapFrom(l => l.Doctor == null ? "" : l.Doctor.Email ?? ""))
            .ForCtorParam(nameof(DoctorPatientLinkDto.DoctorAvatarUrl),
                opt => opt.MapFrom(l => l.Doctor == null ? null : l.Doctor.AvatarUrl))
            .ForCtorParam(nameof(DoctorPatientLinkDto.PatientName),
                opt => opt.MapFrom(l => l.Patient == null ? "" : l.Patient.FullName))
            .ForCtorParam(nameof(DoctorPatientLinkDto.PatientEmail),
                opt => opt.MapFrom(l => l.Patient == null ? "" : l.Patient.Email ?? ""))
            .ForCtorParam(nameof(DoctorPatientLinkDto.PatientAvatarUrl),
                opt => opt.MapFrom(l => l.Patient == null ? null : l.Patient.AvatarUrl))
            .ForCtorParam(nameof(DoctorPatientLinkDto.PatientAge),
                opt => opt.MapFrom(l => l.Patient == null ? (int?)null : l.Patient.GetAge(null)));

        // ── Notification ──
        CreateMap<Notification, NotificationDto>();

        // ── AuditLog ──
        CreateMap<Domain.Entities.AuditLog, AuditLogDto>()
            .ForCtorParam(nameof(AuditLogDto.UserEmail),
                opt => opt.MapFrom(a => a.User == null ? null : a.User.Email));
    }

    private static string Truncate(string text, int max)
    {
        if (string.IsNullOrEmpty(text)) return string.Empty;
        return text.Length <= max ? text : text.Substring(0, max).TrimEnd() + "...";
    }
}
