using System.Security.Cryptography;
using System.Text;
using HEMAX.Application.Common.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace HEMAX.Infrastructure.Services;

public class AesGcmEncryptionService : IEncryptionService
{
    private const byte CurrentVersion = 0x01;
    private const int  NonceSize      = 12;   // 96 bits — GCM standard
    private const int  TagSize        = 16;   // 128 bits — GCM standard
    private const int  KeySize        = 32;   // 256 bits

    private readonly byte[] _masterKey;
    private readonly byte[] _blindIndexKey;
    private readonly ILogger<AesGcmEncryptionService> _logger;

    public AesGcmEncryptionService(
        IConfiguration config,
        ILogger<AesGcmEncryptionService> logger)
    {
        _logger = logger;

        var passphrase = config["Encryption:MasterPassphrase"]
            ?? throw new InvalidOperationException(
                "Encryption:MasterPassphrase is not configured. " +
                "Set it in appsettings.json or via env var ENCRYPTION__MASTERPASSPHRASE.");

        var saltStr = config["Encryption:KeySalt"]
            ?? throw new InvalidOperationException(
                "Encryption:KeySalt is not configured.");

        if (passphrase.Length < 16)
            throw new InvalidOperationException(
                "Encryption:MasterPassphrase must be at least 16 characters.");

        var salt = Encoding.UTF8.GetBytes(saltStr);
        _masterKey = Rfc2898DeriveBytes.Pbkdf2(
            password:        passphrase,
            salt:            salt,
            iterations:      100_000,
            hashAlgorithm:   HashAlgorithmName.SHA256,
            outputLength:    KeySize);

        _blindIndexKey = Rfc2898DeriveBytes.Pbkdf2(
            password:      passphrase + ":blind-index",
            salt:          salt,
            iterations:    100_000,
            hashAlgorithm: HashAlgorithmName.SHA256,
            outputLength:  KeySize);

        _logger.LogInformation(
            "AesGcmEncryptionService initialized (AES-256-GCM, PBKDF2 100k iterations).");
    }

    public string Encrypt(string plaintext)
    {
        if (string.IsNullOrEmpty(plaintext)) return string.Empty;

        var plainBytes = Encoding.UTF8.GetBytes(plaintext);

        // Fresh nonce per encryption — critical for GCM security.
        var nonce = RandomNumberGenerator.GetBytes(NonceSize);
        var cipher = new byte[plainBytes.Length];
        var tag = new byte[TagSize];

        using var aesGcm = new AesGcm(_masterKey, TagSize);
        aesGcm.Encrypt(nonce, plainBytes, cipher, tag);

        // Envelope: [version][nonce][cipher][tag]
        var envelope = new byte[1 + NonceSize + cipher.Length + TagSize];
        envelope[0] = CurrentVersion;
        Buffer.BlockCopy(nonce,  0, envelope, 1,                           NonceSize);
        Buffer.BlockCopy(cipher, 0, envelope, 1 + NonceSize,               cipher.Length);
        Buffer.BlockCopy(tag,    0, envelope, 1 + NonceSize + cipher.Length, TagSize);

        return Convert.ToBase64String(envelope);
    }

    public string Decrypt(string ciphertext)
    {
        if (string.IsNullOrEmpty(ciphertext)) return string.Empty;

        if (!TryDecrypt(ciphertext, out var plaintext))
            throw new CryptographicException(
                "Failed to decrypt: data may be corrupted, tampered with, " +
                "or encrypted with a different key.");

        return plaintext;
    }

    public bool TryDecrypt(string ciphertext, out string plaintext)
    {
        plaintext = string.Empty;
        if (string.IsNullOrEmpty(ciphertext)) return true;

        try
        {
            var envelope = Convert.FromBase64String(ciphertext);
            if (envelope.Length < 1 + NonceSize + TagSize)
            {
                _logger.LogWarning("Ciphertext too short to be a valid envelope.");
                return false;
            }

            var version = envelope[0];
            if (version != CurrentVersion)
            {
                _logger.LogWarning("Unknown encryption version: {Version}", version);
                return false;
            }

            var cipherLen = envelope.Length - 1 - NonceSize - TagSize;
            var nonce  = new byte[NonceSize];
            var cipher = new byte[cipherLen];
            var tag    = new byte[TagSize];

            Buffer.BlockCopy(envelope, 1,                            nonce,  0, NonceSize);
            Buffer.BlockCopy(envelope, 1 + NonceSize,                cipher, 0, cipherLen);
            Buffer.BlockCopy(envelope, 1 + NonceSize + cipherLen,    tag,    0, TagSize);

            var plainBytes = new byte[cipherLen];
            using var aesGcm = new AesGcm(_masterKey, TagSize);
            aesGcm.Decrypt(nonce, cipher, tag, plainBytes);

            plaintext = Encoding.UTF8.GetString(plainBytes);
            return true;
        }
        catch (FormatException)
        {
            return false;
        }
        catch (CryptographicException ex)
        {
            _logger.LogWarning(ex, "GCM authentication failed — data may be tampered.");
            return false;
        }
    }

    public bool IsEncrypted(string? value)
    {
        if (string.IsNullOrEmpty(value)) return false;
        try
        {
            var bytes = Convert.FromBase64String(value);
            return bytes.Length >= 1 + NonceSize + TagSize
                && bytes[0] == CurrentVersion;
        }
        catch (FormatException)
        {
            return false;
        }
    }

    public string ComputeBlindIndex(string value)
    {
        if (string.IsNullOrEmpty(value)) return string.Empty;

        var normalized = value.Trim().ToLowerInvariant();
        var data = Encoding.UTF8.GetBytes(normalized);

        using var hmac = new HMACSHA256(_blindIndexKey);
        var hash = hmac.ComputeHash(data);
        return Convert.ToHexString(hash);
    }
}
