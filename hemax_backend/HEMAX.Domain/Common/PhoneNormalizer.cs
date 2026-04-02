using System.Security.Cryptography;
using System.Text;

namespace HEMAX.Domain.Common;

public static class PhoneNormalizer
{
    public static string Normalize(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw)) return string.Empty;
        var sb = new StringBuilder(raw.Length);
        var hadPlus = false;
        foreach (var ch in raw)
        {
            if (ch == '+' && sb.Length == 0 && !hadPlus)
            {
                sb.Append('+');
                hadPlus = true;
            }
            else if (ch >= '0' && ch <= '9')
            {
                sb.Append(ch);
            }
        }
        return sb.ToString();
    }

    /// <summary>
    /// Returns SHA-256 hex of the normalized phone, or null for blank input.
    ///
    /// <para>
    /// <b>DEPRECATED May 2026.</b> Plain SHA-256 of a phone number is brute-
    /// forceable in seconds — the global E.164 numbering plan has well
    /// under 2^40 distinct values, and a precomputed rainbow table fits
    /// on a USB stick. Production code should use
    /// <c>IEncryptionService.ComputeBlindIndex(PhoneNormalizer.Normalize(raw))</c>
    /// instead, which is keyed HMAC-SHA256 against a secret derived from
    /// <c>Encryption.MasterPassphrase</c>.
    /// </para>
    /// <para>
    /// This method is kept only so legacy data migration paths can recompute
    /// the old hash format to find rows still using the old scheme. All
    /// live write paths in <c>AuthHandlers</c> and <c>ProfileHandlers</c>
    /// have been migrated to <c>ComputeBlindIndex</c>.
    /// </para>
    /// </summary>
    [Obsolete("Use IEncryptionService.ComputeBlindIndex(PhoneNormalizer.Normalize(raw)) — keyed HMAC, not brute-forceable. This plain-SHA-256 helper is kept only for legacy migration scenarios.")]
    public static string? Hash(string? raw)
    {
        var normalized = Normalize(raw);
        if (normalized.Length == 0) return null;
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(normalized));
        return Convert.ToHexString(bytes);
    }
}
