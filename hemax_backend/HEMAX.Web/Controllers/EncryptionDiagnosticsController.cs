using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Enums;
using HEMAX.Infrastructure.Persistence;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;

namespace HEMAX.Web.Controllers;

/// <summary>
/// Diagnostic endpoints to verify encryption is working end-to-end.
/// Useful for the defense demonstration — shows committee that PHI is
/// encrypted at rest, not just claimed to be.
///
/// IMPORTANT: This controller is admin-only AND now feature-flagged.
/// In production, set <c>FeatureFlags:EnableEncryptionDiagnostics</c>
/// to <c>false</c> (the default in the committed appsettings.json).
/// Even an admin can't access these endpoints when the flag is off —
/// every method returns 404, as if the routes didn't exist. We use 404
/// rather than 403 so we don't even confirm the routes' existence to
/// an attacker who's compromised an admin account.
/// </summary>
[ApiController]
[Route("api/diagnostics/encryption")]
[Authorize(Roles = Roles.Administrator)]
[ApiExplorerSettings(GroupName = "diagnostics")]
public class EncryptionDiagnosticsController : ControllerBase, IActionFilter
{
    private readonly IEncryptionService _encryption;
    private readonly HemaxDbContext _db;
    private readonly IConfiguration _config;

    public EncryptionDiagnosticsController(
        IEncryptionService encryption,
        HemaxDbContext db,
        IConfiguration config)
    {
        _encryption = encryption;
        _db = db;
        _config = config;
    }

    /// <summary>
    /// IActionFilter.OnActionExecuting — short-circuit every endpoint on
    /// this controller with 404 unless the feature flag is on. Bug fix
    /// May 2026. We implement IActionFilter directly on the controller
    /// (ASP.NET Core supports filter-interfaces on controllers) instead
    /// of overriding ControllerBase, because ControllerBase doesn't
    /// expose OnActionExecuting as virtual in .NET 8.
    /// </summary>
    void IActionFilter.OnActionExecuting(ActionExecutingContext context)
    {
        var enabled = _config.GetValue<bool?>("FeatureFlags:EnableEncryptionDiagnostics") ?? false;
        if (!enabled)
        {
            context.Result = NotFound();
        }
    }

    void IActionFilter.OnActionExecuted(ActionExecutedContext context) { }

    [HttpPost("roundtrip")]
    public IActionResult Roundtrip([FromBody] RoundtripRequest req)
    {
        var cipher = _encryption.Encrypt(req.Plaintext);
        var decrypted = _encryption.Decrypt(cipher);

        return Ok(new
        {
            input          = req.Plaintext,
            ciphertext     = cipher,
            ciphertextSize = cipher.Length,
            decrypted      = decrypted,
            roundtripOk    = decrypted == req.Plaintext,
            algorithm      = "AES-256-GCM",
            envelope       = "version(1B) || nonce(12B) || ciphertext(NB) || tag(16B), base64",
        });
    }

    /// <summary>
    /// Show that two encryptions of the same plaintext produce DIFFERENT
    /// ciphertexts (semantic security via random per-row nonces).
    /// </summary>
    [HttpGet("nonce-uniqueness-demo")]
    public IActionResult NonceUniqueness([FromQuery] string plaintext = "Patient HGB 12.5")
    {
        var c1 = _encryption.Encrypt(plaintext);
        var c2 = _encryption.Encrypt(plaintext);
        var c3 = _encryption.Encrypt(plaintext);

        return Ok(new
        {
            plaintext,
            ciphertext1 = c1,
            ciphertext2 = c2,
            ciphertext3 = c3,
            allDifferent = c1 != c2 && c2 != c3 && c1 != c3,
            note = "Same input → different output proves nonce-based semantic security."
        });
    }

    [HttpGet("verify-stored/{analysisId:guid}")]
    public async Task<IActionResult> VerifyStored(Guid analysisId, CancellationToken ct)
    {
        var raw = await _db.Database
            .SqlQuery<RawAnalysisRow>($@"
                SELECT
                    Id            AS Id,
                    RawInputJson  AS RawInputJsonStored,
                    ResultJson    AS ResultJsonStored,
                    DoctorNote    AS DoctorNoteStored
                FROM Analyses
                WHERE Id = {analysisId}")
            .FirstOrDefaultAsync(ct);

        if (raw is null)
            return NotFound(new { error = "Analysis not found" });

        var via_ef = await _db.Analyses
            .AsNoTracking()
            .FirstOrDefaultAsync(a => a.Id == analysisId, ct);

        return Ok(new
        {
            analysisId,
            asStoredInDatabase = new
            {
                rawInputJson_first100 = Truncate(raw.RawInputJsonStored, 100),
                resultJson_first100   = Truncate(raw.ResultJsonStored, 100),
                isRawInputEncrypted   = _encryption.IsEncrypted(raw.RawInputJsonStored),
                isResultEncrypted     = _encryption.IsEncrypted(raw.ResultJsonStored),
                isDoctorNoteEncrypted = _encryption.IsEncrypted(raw.DoctorNoteStored),
            },
            asReturnedByApi = new
            {
                rawInputJson_first100 = Truncate(via_ef?.RawInputJson, 100),
                resultJson_first100   = Truncate(via_ef?.ResultJson, 100),
                doctorNote            = Truncate(via_ef?.DoctorNote, 100),
            },
            note = "Database shows base64 ciphertext; API decrypts transparently. " +
                   "Even a DB admin with raw SQL access cannot read PHI."
        });
    }

    private static string? Truncate(string? text, int max)
    {
        if (string.IsNullOrEmpty(text)) return text;
        return text.Length <= max ? text : text.Substring(0, max) + "...";
    }

    public record RoundtripRequest(string Plaintext);

    private class RawAnalysisRow
    {
        public Guid Id { get; set; }
        public string RawInputJsonStored { get; set; } = string.Empty;
        public string ResultJsonStored   { get; set; } = string.Empty;
        public string? DoctorNoteStored  { get; set; }
    }
}
