using AutoMapper;
using HEMAX.Application.Auth;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Application.Common.Models;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using HEMAX.Infrastructure.Files;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.Users;

public class UpdateProfileHandler : IRequestHandler<UpdateProfileCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IIdentityService _identity;

    public UpdateProfileHandler(IHemaxDbContext db, ICurrentUserService current, IIdentityService identity)
    {
        _db = db; _current = current; _identity = identity;
    }

    public async Task Handle(UpdateProfileCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var user = await _identity.GetUserByIdAsync(_current.UserId.Value, ct)
            ?? throw new UnauthorizedException();

        user.FirstName   = cmd.FirstName.Trim();
        user.LastName    = cmd.LastName.Trim();
        user.DateOfBirth = cmd.DateOfBirth;
        user.Sex         = cmd.Sex;
        user.UpdatedAt   = DateTimeOffset.UtcNow;

        await _db.SaveChangesAsync(ct);
    }
}

public class UpdateAvatarHandler : IRequestHandler<UpdateAvatarCommand, string>
{
    private const long MaxAvatarBytes = 5 * 1024 * 1024; // 5 MB

    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IIdentityService _identity;
    private readonly IFileStorageService _storage;
    private readonly IFileSignatureValidator _signatures;

    public UpdateAvatarHandler(IHemaxDbContext db, ICurrentUserService current,
        IIdentityService identity, IFileStorageService storage,
        IFileSignatureValidator signatures)
    {
        _db = db; _current = current; _identity = identity;
        _storage = storage; _signatures = signatures;
    }

    public async Task<string> Handle(UpdateAvatarCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        await _signatures.ValidateAsync(
            cmd.FileStream, cmd.ContentType, FileKind.Image,
            maxBytes: MaxAvatarBytes, ct: ct);

        var (storageKey, publicUrl) = await _storage.SaveAsync(
            cmd.FileStream, cmd.FileName, cmd.ContentType, ct,
            category: "avatars");

        // Track in FileAsset
        _db.FileAssets.Add(new FileAsset
        {
            OwnerId     = _current.UserId.Value,
            Type        = FileAssetType.Avatar,
            FileName    = cmd.FileName,
            ContentType = cmd.ContentType,
            StorageKey  = storageKey,
            PublicUrl   = publicUrl,
        });

        // Update user
        var user = await _identity.GetUserByIdAsync(_current.UserId.Value, ct)
            ?? throw new UnauthorizedException();
        user.AvatarUrl = publicUrl;

        await _db.SaveChangesAsync(ct);
        return publicUrl ?? storageKey;
    }
}

public class GetAllUsersHandler : IRequestHandler<GetAllUsersQuery, PagedResult<UserDto>>
{
    private readonly IHemaxDbContext _db;
    private readonly Microsoft.AspNetCore.Identity.UserManager<ApplicationUser> _userManager;
    private readonly IMapper _mapper;

    public GetAllUsersHandler(IHemaxDbContext db,
        Microsoft.AspNetCore.Identity.UserManager<ApplicationUser> userManager, IMapper mapper)
    {
        _db = db; _userManager = userManager; _mapper = mapper;
    }

    public async Task<PagedResult<UserDto>> Handle(GetAllUsersQuery q, CancellationToken ct)
    {
        var query = _db.Users.AsQueryable();

        if (!string.IsNullOrWhiteSpace(q.Search))
        {
            var s = q.Search.Trim();
            query = query.Where(u =>
                (u.Email != null && u.Email.Contains(s)) ||
                u.FirstName.Contains(s) ||
                u.LastName.Contains(s));
        }

        var total = await query.CountAsync(ct);
        var users = await query
            .OrderByDescending(u => u.CreatedAt)
            .Skip(q.Page.Skip).Take(q.Page.Take)
            .ToListAsync(ct);

        var dtos = new List<UserDto>(users.Count);
        foreach (var u in users)
        {
            var roles = await _userManager.GetRolesAsync(u);

            if (!string.IsNullOrEmpty(q.RoleFilter) && !roles.Contains(q.RoleFilter))
                continue;

            dtos.Add(new UserDto(
                u.Id, u.Email!, u.FirstName, u.LastName, u.DateOfBirth, u.Sex,
                u.AvatarUrl, roles.ToList().AsReadOnly(),
                u.EmailConfirmed, u.CreatedAt));
        }

        return new PagedResult<UserDto>
        {
            Items      = dtos.AsReadOnly(),
            Page       = q.Page.Page,
            PageSize   = q.Page.PageSize,
            TotalItems = total,
        };
    }
}

public class SetUserBanStatusHandler : IRequestHandler<SetUserBanStatusCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly IIdentityService _identity;
    private readonly IAuditService _audit;

    public SetUserBanStatusHandler(IHemaxDbContext db, IIdentityService identity, IAuditService audit)
    {
        _db = db; _identity = identity; _audit = audit;
    }

    public async Task Handle(SetUserBanStatusCommand cmd, CancellationToken ct)
    {
        var user = await _identity.GetUserByIdAsync(cmd.UserId, ct)
            ?? throw new EntityNotFoundException("User", cmd.UserId);

        user.IsBanned  = cmd.IsBanned;
        user.BanReason = cmd.IsBanned ? cmd.Reason : null;

        await _db.SaveChangesAsync(ct);

        await _audit.LogAsync(AuditAction.UserBanned, "User", user.Id,
            new { isBanned = cmd.IsBanned, reason = cmd.Reason }, ct);
    }
}

public class ChangeUserRoleHandler : IRequestHandler<ChangeUserRoleCommand>
{
    private readonly IIdentityService _identity;
    private readonly Microsoft.AspNetCore.Identity.UserManager<ApplicationUser> _userManager;
    private readonly IAuditService _audit;

    public ChangeUserRoleHandler(IIdentityService identity,
        Microsoft.AspNetCore.Identity.UserManager<ApplicationUser> userManager, IAuditService audit)
    {
        _identity = identity; _userManager = userManager; _audit = audit;
    }

    public async Task Handle(ChangeUserRoleCommand cmd, CancellationToken ct)
    {
        if (!Roles.All.Contains(cmd.NewRole))
            throw new BusinessRuleViolationException("INVALID_ROLE",
                $"Role '{cmd.NewRole}' is not valid");

        var user = await _identity.GetUserByIdAsync(cmd.UserId, ct)
            ?? throw new EntityNotFoundException("User", cmd.UserId);

        var current = await _userManager.GetRolesAsync(user);
        await _userManager.RemoveFromRolesAsync(user, current);
        await _identity.AddToRoleAsync(user, cmd.NewRole, ct);

        await _audit.LogAsync(AuditAction.RoleChanged, "User", user.Id,
            new { oldRoles = current, newRole = cmd.NewRole }, ct);
    }
}
