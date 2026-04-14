using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Infrastructure.Identity;

public class IdentityService : IIdentityService
{
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly RoleManager<ApplicationRole> _roleManager;
    private readonly SignInManager<ApplicationUser> _signInManager;

    public IdentityService(
        UserManager<ApplicationUser> userManager,
        RoleManager<ApplicationRole> roleManager,
        SignInManager<ApplicationUser> signInManager)
    {
        _userManager = userManager;
        _roleManager = roleManager;
        _signInManager = signInManager;
    }

    public async Task<(bool Success, string[] Errors, ApplicationUser? User)> RegisterAsync(
        string email, string password, string firstName, string lastName,
        DateOnly? dob, Sex sex, CancellationToken ct)
    {
        var existing = await _userManager.FindByEmailAsync(email);
        if (existing is not null)
            return (false, new[] { "Email is already registered" }, null);

        var user = new ApplicationUser
        {
            UserName     = email,
            Email        = email,
            FirstName    = firstName,
            LastName     = lastName,
            DateOfBirth  = dob,
            Sex          = sex,
            CreatedAt    = DateTimeOffset.UtcNow,
        };

        var result = await _userManager.CreateAsync(user, password);
        if (!result.Succeeded)
            return (false, result.Errors.Select(e => e.Description).ToArray(), null);

        return (true, Array.Empty<string>(), user);
    }

    public async Task<(bool Success, ApplicationUser? User)> ValidateCredentialsAsync(
        string email, string password, CancellationToken ct)
    {
        var user = await _userManager.FindByEmailAsync(email);
        if (user is null) return (false, null);

        var ok = await _userManager.CheckPasswordAsync(user, password);
        return (ok, ok ? user : null);
    }

    public async Task<IList<string>> GetUserRolesAsync(ApplicationUser user, CancellationToken ct)
        => await _userManager.GetRolesAsync(user);

    public async Task AddToRoleAsync(ApplicationUser user, string role, CancellationToken ct)
    {
        if (!await _roleManager.RoleExistsAsync(role))
            await _roleManager.CreateAsync(new ApplicationRole(role));

        if (!await _userManager.IsInRoleAsync(user, role))
            await _userManager.AddToRoleAsync(user, role);
    }

    public async Task<bool> ChangePasswordAsync(
        Guid userId, string currentPassword, string newPassword, CancellationToken ct)
    {
        var user = await _userManager.FindByIdAsync(userId.ToString());
        if (user is null) return false;

        var result = await _userManager.ChangePasswordAsync(user, currentPassword, newPassword);
        return result.Succeeded;
    }

    public Task<ApplicationUser?> GetUserByEmailAsync(string email, CancellationToken ct)
        => _userManager.FindByEmailAsync(email);

    public Task<ApplicationUser?> GetUserByIdAsync(Guid id, CancellationToken ct)
        => _userManager.FindByIdAsync(id.ToString());
}
