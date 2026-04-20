using System.Text;
using System.Threading.RateLimiting;
using HEMAX.Application;
using HEMAX.Domain.Enums;
using HEMAX.Infrastructure;
using HEMAX.Infrastructure.Persistence;
using HEMAX.Infrastructure.Persistence.Seed;
using HEMAX.Web.Middleware;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using Serilog;


var builder = WebApplication.CreateBuilder(args);

Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .WriteTo.Console()
    .WriteTo.File("logs/hemax-.log", rollingInterval: RollingInterval.Day)
    .CreateLogger();
builder.Host.UseSerilog();

builder.Services.AddApplication();
builder.Services.AddInfrastructure(builder.Configuration);

var jwtKey      = builder.Configuration["Jwt:Key"]
    ?? throw new InvalidOperationException("Jwt:Key must be set in configuration");
var jwtIssuer   = builder.Configuration["Jwt:Issuer"]   ?? "hemax-backend";
var jwtAudience = builder.Configuration["Jwt:Audience"] ?? "hemax-clients";

builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(opt =>
    {
        opt.RequireHttpsMetadata = !builder.Environment.IsDevelopment();
        opt.SaveToken = true;
        opt.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer           = true,
            ValidateAudience         = true,
            ValidateLifetime         = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer       = jwtIssuer,
            ValidAudience     = jwtAudience,
            IssuerSigningKey  = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
            ClockSkew         = TimeSpan.FromMinutes(2),
        };
    });

builder.Services.AddAuthorization(opt =>
{
    opt.AddPolicy("AdminOnly",   p => p.RequireRole(Roles.Administrator));
    opt.AddPolicy("DoctorOnly",  p => p.RequireRole(Roles.Doctor, Roles.Administrator));
});

builder.Services.AddControllers()
    .AddJsonOptions(o =>
    {
        o.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
        o.JsonSerializerOptions.Converters.Add(
            new System.Text.Json.Serialization.JsonStringEnumConverter());
    });

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(o =>
{
    o.SwaggerDoc("v1", new OpenApiInfo
    {
        Title       = "HEMAX Backend API",
        Version     = "v1",
        Description = "REST API for HEMAX medical analysis platform with auth, " +
                      "analyses tracking, blog, doctor-patient relationships, " +
                      "notifications, and admin functions.",
    });

    var jwtScheme = new OpenApiSecurityScheme
    {
        Name         = "Authorization",
        Type         = SecuritySchemeType.Http,
        Scheme       = "Bearer",
        BearerFormat = "JWT",
        In           = ParameterLocation.Header,
        Description  = "Enter JWT token (without 'Bearer ' prefix).",
        Reference    = new OpenApiReference
        {
            Type = ReferenceType.SecurityScheme,
            Id   = "Bearer",
        },
    };
    o.AddSecurityDefinition("Bearer", jwtScheme);
    o.AddSecurityRequirement(new OpenApiSecurityRequirement { { jwtScheme, Array.Empty<string>() } });
});

builder.Services.AddCors(o =>
{
    o.AddPolicy("DevCors", p => p
        .SetIsOriginAllowed(origin =>
        {
            // localhost / explicit dev ports
            if (string.IsNullOrEmpty(origin)) return false;
            try
            {
                var u = new Uri(origin);
                if (u.Host is "localhost" or "127.0.0.1") return true;

                if (System.Net.IPAddress.TryParse(u.Host, out var ip))
                {
                    var b = ip.GetAddressBytes();
                    if (b.Length == 4)
                    {
                        if (b[0] == 192 && b[1] == 168) return true;
                        if (b[0] == 10) return true;
                        if (b[0] == 172 && b[1] >= 16 && b[1] <= 31) return true;
                    }
                }
                return false;
            }
            catch { return false; }
        })
        .AllowAnyHeader()
        .AllowAnyMethod()
        .AllowCredentials());
});

builder.Services.AddRateLimiter(opt =>
{
    // Global: 100 requests / minute per IP
    opt.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(ctx =>
        RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: ctx.Connection.RemoteIpAddress?.ToString() ?? "anon",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit       = 100,
                Window            = TimeSpan.FromMinutes(1),
                QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                QueueLimit        = 0,
            }));

    opt.AddPolicy("AuthPolicy", ctx =>
        RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: ctx.Connection.RemoteIpAddress?.ToString() ?? "anon",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = 10,
                Window      = TimeSpan.FromMinutes(1),
            }));

    opt.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
});


var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var sp = scope.ServiceProvider;
    var db = sp.GetRequiredService<HemaxDbContext>();

    if (app.Configuration.GetValue("Database:AutoMigrate", true))
    {
        await db.Database.MigrateAsync();
    }

    try
    {
        await db.Database.ExecuteSqlRawAsync(@"
            IF COL_LENGTH('UserProfiles', 'PhoneHash') IS NULL
            BEGIN
                ALTER TABLE [UserProfiles] ADD [PhoneHash] nvarchar(64) NULL;
            END");

        await db.Database.ExecuteSqlRawAsync(@"
            IF NOT EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE name = 'IX_UserProfiles_PhoneHash_Unique'
                  AND object_id = OBJECT_ID('UserProfiles')
            )
            BEGIN
                CREATE UNIQUE INDEX [IX_UserProfiles_PhoneHash_Unique]
                    ON [UserProfiles]([PhoneHash])
                    WHERE [PhoneHash] IS NOT NULL;
            END");

        Log.Information("Schema sync OK: UserProfiles.PhoneHash + unique index ensured.");
    }
    catch (Exception ex)
    {
        Log.Warning(ex, "Schema sync failed (non-fatal). " +
            "Phone-uniqueness DB constraint may be missing.");
    }

    if (app.Configuration.GetValue("Database:Seed", true))
    {
        await DatabaseSeeder.SeedAsync(sp);
    }
}

app.UseSerilogRequestLogging();
app.UseMiddleware<ExceptionHandlingMiddleware>();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(o =>
    {
        o.SwaggerEndpoint("/swagger/v1/swagger.json", "HEMAX API v1");
        o.RoutePrefix = "swagger";
    });
    app.UseCors("DevCors");
}

app.UseRateLimiter();

var fileProvider = builder.Configuration["FileStorage:Provider"] ?? "LocalDisk";
if (string.Equals(fileProvider, "LocalDisk", StringComparison.OrdinalIgnoreCase))
{
    var uploadRoot = Path.GetFullPath(builder.Configuration["FileStorage:Root"] ?? "./uploads");
    Directory.CreateDirectory(uploadRoot);  // ensure it exists, don't crash startup
    app.UseStaticFiles(new StaticFileOptions
    {
        FileProvider = new Microsoft.Extensions.FileProviders.PhysicalFileProvider(uploadRoot),
        RequestPath = builder.Configuration["FileStorage:PublicBaseUrl"] ?? "/files",
    });
}

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.MapGet("/", () => Results.Redirect("/swagger"));

app.Run();
