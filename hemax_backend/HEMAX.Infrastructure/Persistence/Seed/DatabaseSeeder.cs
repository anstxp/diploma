using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace HEMAX.Infrastructure.Persistence.Seed;

public static class DatabaseSeeder
{
    public static async Task SeedAsync(IServiceProvider sp)
    {
        var logger      = sp.GetRequiredService<ILogger<HemaxDbContext>>();
        var roleManager = sp.GetRequiredService<RoleManager<ApplicationRole>>();
        var userManager = sp.GetRequiredService<UserManager<ApplicationUser>>();
        var config      = sp.GetRequiredService<IConfiguration>();

        // 1. Roles
        foreach (var roleName in Roles.All)
        {
            if (!await roleManager.RoleExistsAsync(roleName))
            {
                var role = new ApplicationRole(roleName)
                {
                    Description = roleName switch
                    {
                        Roles.Administrator => "Full system access",
                        Roles.Doctor        => "Can view assigned patients' analyses and annotate",
                        Roles.User          => "Default user role — patient",
                        _                   => null,
                    }
                };
                await roleManager.CreateAsync(role);
                logger.LogInformation("Created role {Role}", roleName);
            }
        }

        // 2. Default admin user
        var adminEmail    = config["Seed:AdminEmail"]    ?? "admin@hemax.local";
        var adminPassword = config["Seed:AdminPassword"] ?? "Admin#12345";

        var admin = await userManager.FindByEmailAsync(adminEmail);
        if (admin is null)
        {
            admin = new ApplicationUser
            {
                UserName        = adminEmail,
                Email           = adminEmail,
                EmailConfirmed  = true,
                FirstName       = "HEMAX",
                LastName        = "Administrator",
                Sex             = Sex.Unknown,
                CreatedAt       = DateTimeOffset.UtcNow,
            };

            var result = await userManager.CreateAsync(admin, adminPassword);
            if (result.Succeeded)
            {
                await userManager.AddToRoleAsync(admin, Roles.Administrator);
                logger.LogInformation("Created default admin: {Email}", adminEmail);
                logger.LogWarning(
                    "⚠ Default admin password is '{Password}'. CHANGE IT in production!",
                    adminPassword);
            }
            else
            {
                logger.LogError("Failed to create admin: {Errors}",
                    string.Join("; ", result.Errors.Select(e => e.Description)));
            }
        }

        // 3. Sample doctor (only in dev)
        if (config.GetValue("Seed:CreateSampleData", false))
        {
            await SeedSampleDoctorAsync(userManager, logger);
            await SeedSamplePatientAsync(userManager, logger);
        }
    }

    private static async Task SeedSampleDoctorAsync(
        UserManager<ApplicationUser> userManager, ILogger logger)
    {
        const string email    = "doctor@hemax.local";
        const string password = "Doctor#12345";

        if (await userManager.FindByEmailAsync(email) is not null) return;

        var doctor = new ApplicationUser
        {
            UserName       = email,
            Email          = email,
            EmailConfirmed = true,
            FirstName      = "Олена",
            LastName       = "Іваненко",
            Sex            = Sex.Female,
            CreatedAt      = DateTimeOffset.UtcNow,
        };
        var result = await userManager.CreateAsync(doctor, password);
        if (result.Succeeded)
        {
            await userManager.AddToRoleAsync(doctor, Roles.Doctor);
            logger.LogInformation("Created sample doctor: {Email}", email);
        }
    }

    private static async Task SeedSamplePatientAsync(
        UserManager<ApplicationUser> userManager, ILogger logger)
    {
        const string email    = "patient@hemax.local";
        const string password = "Patient#12345";

        if (await userManager.FindByEmailAsync(email) is not null) return;

        var patient = new ApplicationUser
        {
            UserName       = email,
            Email          = email,
            EmailConfirmed = true,
            FirstName      = "Тарас",
            LastName       = "Шевченко",
            DateOfBirth    = new DateOnly(1985, 3, 9),
            Sex            = Sex.Male,
            CreatedAt      = DateTimeOffset.UtcNow,
        };
        var result = await userManager.CreateAsync(patient, password);
        if (result.Succeeded)
        {
            await userManager.AddToRoleAsync(patient, Roles.User);
            logger.LogInformation("Created sample patient: {Email}", email);
        }
    }
}
