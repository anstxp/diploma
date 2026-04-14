using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Entities;
using HEMAX.Infrastructure.Files;
using HEMAX.Infrastructure.HemaxApi;
using HEMAX.Infrastructure.Identity;
using HEMAX.Infrastructure.Persistence;
using HEMAX.Infrastructure.Services;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace HEMAX.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services, IConfiguration config)
    {
        services.AddSingleton<IEncryptionService, AesGcmEncryptionService>();

        // ── DbContext ──
        var conn = config.GetConnectionString("HemaxDb")
            ?? throw new InvalidOperationException("Connection string 'HemaxDb' is missing");

        services.AddDbContext<HemaxDbContext>(opt =>
            opt.UseSqlServer(conn, sql =>
            {
                sql.MigrationsAssembly(typeof(HemaxDbContext).Assembly.FullName);
                sql.EnableRetryOnFailure(maxRetryCount: 3);
            }));

        services.AddScoped<IHemaxDbContext>(sp => sp.GetRequiredService<HemaxDbContext>());

        services
            .AddIdentityCore<ApplicationUser>(opt =>
            {
                opt.Password.RequireDigit           = true;
                opt.Password.RequireLowercase       = true;
                opt.Password.RequireUppercase       = true;
                opt.Password.RequireNonAlphanumeric = false;
                opt.Password.RequiredLength         = 8;

                opt.User.RequireUniqueEmail = true;

                opt.SignIn.RequireConfirmedEmail = false; // we use our own EmailVerification
            })
            .AddRoles<ApplicationRole>()
            .AddEntityFrameworkStores<HemaxDbContext>()
            .AddSignInManager()
            .AddDefaultTokenProviders();

        services.AddScoped<IIdentityService, IdentityService>();
        services.AddSingleton<ITokenService, JwtTokenService>();

        // ── Common services ──
        services.AddSingleton<IDateTimeProvider, SystemDateTimeProvider>();
        services.AddHttpContextAccessor();
        services.AddScoped<ICurrentUserService, CurrentUserService>();
        services.AddScoped<IAuditService, AuditService>();
        services.AddScoped<INotificationService, NotificationService>();
        services.AddScoped<IEmailService, SmtpEmailService>();

        var provider = config["FileStorage:Provider"] ?? "LocalDisk";
        if (string.Equals(provider, "AzureBlob", StringComparison.OrdinalIgnoreCase))
        {
            services.AddSingleton<IFileStorageService, AzureBlobFileStorage>();
            services.AddSingleton<IFileUrlGenerator, AzureBlobUrlGenerator>();
        }
        else
        {
            services.AddSingleton<IFileStorageService, LocalDiskFileStorage>();
            services.AddSingleton<IFileUrlGenerator, LocalDiskUrlGenerator>();
        }

        // ── PDF lab report parser ──
        services.AddSingleton<IPdfLabReportParser, PdfPigLabReportParser>();

        services.AddSingleton<IFileSignatureValidator, FileSignatureValidator>();

        // ── HEMAX Python service clients ──
        services.AddHttpClient<IHemaxCbcClient, HemaxCbcClient>(c =>
        {
            c.BaseAddress = new Uri(config["Hemax:CbcBaseUrl"] ?? "http://localhost:8001");
            c.Timeout     = TimeSpan.FromSeconds(15);
        });
        services.AddHttpClient<IHemaxChemClient, HemaxChemClient>(c =>
        {
            c.BaseAddress = new Uri(config["Hemax:ChemBaseUrl"] ?? "http://localhost:8101");
            c.Timeout     = TimeSpan.FromSeconds(15);
        });
        services.AddHttpClient<IHemaxRiskClient, HemaxRiskClient>(c =>
        {
            c.BaseAddress = new Uri(config["Hemax:RiskBaseUrl"] ?? "http://localhost:8002");
            c.Timeout     = TimeSpan.FromSeconds(15);
        });
        services.AddHttpClient<IHemaxNeuroClient, HemaxNeuroClient>(c =>
        {
            c.BaseAddress = new Uri(config["Hemax:NeuroBaseUrl"] ?? "http://localhost:8003");
            c.Timeout     = TimeSpan.FromSeconds(15);
        });
        services.AddHttpClient<IHemaxDermaClient, HemaxDermaClient>(c =>
        {
            c.BaseAddress = new Uri(config["Hemax:DermaBaseUrl"] ?? "http://localhost:8004");
            c.Timeout     = TimeSpan.FromSeconds(60);  // tolerant of cold start
        });

        services.AddScoped<IHemaxApiFacade, HemaxApiFacade>();

        return services;
    }
}
