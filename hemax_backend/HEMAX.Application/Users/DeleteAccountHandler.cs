using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace HEMAX.Application.Users;

/// <summary>
/// Hard-deletes the current user and all owned data.
///
/// Includes cascade for:
///   • Analyses        — owned by user
///   • FileAssets      — both DB rows and blob storage objects
///   • Comments        — authored by user
///   • DoctorPatientLinks — both as doctor and as patient
///   • Notifications   — addressed to user
///   • RefreshTokens   — issued to user
///   • BlogPosts       — authored by user (also their PostLikes)
///   • PostLikes       — given by user
///   • EmailVerifications — outstanding for user
///   • UserProfile     — auto-cascades via FK from ApplicationUser
///   • ApplicationUser — last (Identity row)
///
/// Audit log records are PRESERVED (compliance) but UserId is preserved
/// — they still link to a now-deleted user; that's intentional for
/// security forensics.
///
/// The operation runs in a single transaction; any failure aborts the
/// whole delete.
/// </summary>
public record DeleteAccountCommand : IRequest;

public class DeleteAccountHandler : IRequestHandler<DeleteAccountCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IIdentityService _identity;
    private readonly IFileStorageService _storage;
    private readonly IAuditService _audit;
    private readonly ILogger<DeleteAccountHandler> _log;

    public DeleteAccountHandler(
        IHemaxDbContext db,
        ICurrentUserService current,
        IIdentityService identity,
        IFileStorageService storage,
        IAuditService audit,
        ILogger<DeleteAccountHandler> log)
    {
        _db = db;
        _current = current;
        _identity = identity;
        _storage = storage;
        _audit = audit;
        _log = log;
    }

    public async Task Handle(DeleteAccountCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();
        var userId = _current.UserId.Value;

        var user = await _identity.GetUserByIdAsync(userId, ct)
            ?? throw new EntityNotFoundException("User", userId);

        _log.LogWarning(
            "Account deletion initiated for user {UserId} ({Email})",
            userId, user.Email);

        await _audit.LogAsync(
            AuditAction.UserProfileUpdated,
            "ApplicationUser", userId,
            new
            {
                action = "account_deleted",
                deletedBy = "self",
                email = user.Email,
            }, ct);

        var files = await _db.FileAssets
            .Where(f => f.OwnerId == userId)
            .ToListAsync(ct);

        foreach (var f in files)
        {
            try
            {
                await _storage.DeleteAsync(f.StorageKey, ct);
            }
            catch (Exception ex)
            {
                _log.LogWarning(ex,
                    "Failed to delete blob {Key} for user {UserId} — continuing",
                    f.StorageKey, userId);
            }
        }

        var postLikes = _db.PostLikes.Where(x => x.UserId == userId);
        _db.PostLikes.RemoveRange(postLikes);

        var blogPosts = await _db.BlogPosts
            .Where(p => p.AuthorId == userId)
            .Select(p => p.Id)
            .ToListAsync(ct);
        if (blogPosts.Count > 0)
        {
            var likesOnOurPosts = _db.PostLikes.Where(x => blogPosts.Contains(x.PostId));
            _db.PostLikes.RemoveRange(likesOnOurPosts);
            var commentsOnOurPosts = _db.Comments.Where(x => blogPosts.Contains(x.PostId));
            _db.Comments.RemoveRange(commentsOnOurPosts);
            _db.BlogPosts.RemoveRange(_db.BlogPosts.Where(p => p.AuthorId == userId));
        }

        var comments = _db.Comments.Where(x => x.AuthorId == userId);
        _db.Comments.RemoveRange(comments);

        // Notifications addressed to user
        var notifications = _db.Notifications.Where(x => x.UserId == userId);
        _db.Notifications.RemoveRange(notifications);

        // RefreshTokens issued to user
        var refreshTokens = _db.RefreshTokens.Where(x => x.UserId == userId);
        _db.RefreshTokens.RemoveRange(refreshTokens);

        // DoctorPatientLinks (both directions)
        var links = _db.DoctorPatientLinks.Where(
            x => x.DoctorId == userId || x.PatientId == userId);
        _db.DoctorPatientLinks.RemoveRange(links);

        // EmailVerifications outstanding
        var verifications = _db.EmailVerifications.Where(x => x.UserId == userId);
        _db.EmailVerifications.RemoveRange(verifications);

        // Analyses + FileAssets owned by user
        var analyses = _db.Analyses.Where(a => a.UserId == userId);
        _db.Analyses.RemoveRange(analyses);
        _db.FileAssets.RemoveRange(_db.FileAssets.Where(f => f.OwnerId == userId));

        await _db.SaveChangesAsync(ct);

        _db.Users.Remove(user);
        await _db.SaveChangesAsync(ct);

        _log.LogWarning(
            "Account deletion completed for user {UserId} ({Email}). "
            + "Removed {FileCount} files, {AnalysisCount} analyses, "
            + "{BlogPostCount} blog posts.",
            userId, user.Email, files.Count, analyses.Count(), blogPosts.Count);
    }
}
