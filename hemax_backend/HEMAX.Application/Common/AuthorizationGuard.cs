using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Enums;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Common;

internal static class AuthorizationGuard
{
    public static async Task EnsureCanViewUserDataAsync(
        IHemaxDbContext db,
        ICurrentUserService current,
        Guid targetUserId,
        CancellationToken ct)
    {
        if (current.UserId is null) throw new UnauthorizedException();

        // Self-access — always allowed.
        if (targetUserId == current.UserId.Value) return;

        // Admin override.
        if (current.IsInRole(Roles.Administrator)) return;

        // Doctor needs accepted link.
        if (current.IsInRole(Roles.Doctor))
        {
            var hasLink = await db.DoctorPatientLinks.AnyAsync(l =>
                l.DoctorId  == current.UserId &&
                l.PatientId == targetUserId &&
                l.Status    == DoctorPatientStatus.Accepted, ct);

            if (hasLink) return;
            throw new ForbiddenException("No accepted patient link.");
        }

        throw new ForbiddenException();
    }
}
