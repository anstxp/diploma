using FluentAssertions;
using HEMAX.Infrastructure.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging.Abstractions;
using System.Security.Cryptography;
using Xunit;

namespace HEMAX.Tests.Encryption;

public class AesGcmEncryptionServiceTests
{
    private static AesGcmEncryptionService CreateService(
        string passphrase = "test-passphrase-for-aes256-gcm-tests-must-be-32+",
        string salt = "test-salt-for-key-derivation")
    {
        var config = new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Encryption:MasterPassphrase"] = passphrase,
                ["Encryption:KeySalt"]          = salt,
            })
            .Build();

        return new AesGcmEncryptionService(config, NullLogger<AesGcmEncryptionService>.Instance);
    }

    [Fact]
    public void Encrypt_then_Decrypt_returns_original_plaintext()
    {
        var svc = CreateService();
        var plain = "Patient John Doe — HGB 9.5, RBC 3.2, MCV 68 — iron deficiency anemia";

        var cipher = svc.Encrypt(plain);
        var decrypted = svc.Decrypt(cipher);

        decrypted.Should().Be(plain);
    }

    [Fact]
    public void Encrypt_same_plaintext_twice_produces_different_ciphertexts()
    {
        var svc = CreateService();
        var plain = "PHI: blood test result";

        var c1 = svc.Encrypt(plain);
        var c2 = svc.Encrypt(plain);

        // Different nonces → different ciphertexts (semantic security)
        c1.Should().NotBe(c2);
        svc.Decrypt(c1).Should().Be(plain);
        svc.Decrypt(c2).Should().Be(plain);
    }

    [Fact]
    public void Encrypt_handles_empty_string()
    {
        var svc = CreateService();
        svc.Encrypt(string.Empty).Should().Be(string.Empty);
    }

    [Fact]
    public void Encrypt_handles_unicode()
    {
        var svc = CreateService();
        var plain = "Пацієнт: рівень гемоглобіну 9.5 г/дл — анемія 🩸";

        var cipher = svc.Encrypt(plain);
        var decrypted = svc.Decrypt(cipher);

        decrypted.Should().Be(plain);
    }

    [Fact]
    public void Encrypt_handles_large_json_payload()
    {
        var svc = CreateService();
        var json = "{\"labs\":{" + string.Join(",",
            Enumerable.Range(0, 50).Select(i => $"\"lab_{i}\":{i * 1.234}")
        ) + "}}";

        var cipher = svc.Encrypt(json);
        var decrypted = svc.Decrypt(cipher);

        decrypted.Should().Be(json);
    }

    [Fact]
    public void Decrypt_with_different_key_throws()
    {
        var svc1 = CreateService(passphrase: "passphrase-one-aaaaaaaaaaaaaaaaaaaaaaaaa");
        var svc2 = CreateService(passphrase: "passphrase-two-bbbbbbbbbbbbbbbbbbbbbbbbb");

        var cipher = svc1.Encrypt("secret data");

        Action act = () => svc2.Decrypt(cipher);
        act.Should().Throw<CryptographicException>();
    }

    [Fact]
    public void TryDecrypt_with_different_key_returns_false()
    {
        var svc1 = CreateService(passphrase: "key-one-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
        var svc2 = CreateService(passphrase: "key-two-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb");

        var cipher = svc1.Encrypt("secret");

        svc2.TryDecrypt(cipher, out var plain).Should().BeFalse();
        plain.Should().Be(string.Empty);
    }

    [Fact]
    public void Decrypt_tampered_ciphertext_throws()
    {
        var svc = CreateService();
        var cipher = svc.Encrypt("authentic medical data");

        var bytes = Convert.FromBase64String(cipher);
        bytes[bytes.Length / 2] ^= 0xFF;
        var tampered = Convert.ToBase64String(bytes);

        Action act = () => svc.Decrypt(tampered);
        act.Should().Throw<CryptographicException>(
            "GCM authentication tag must detect tampering");
    }

    [Fact]
    public void TryDecrypt_returns_false_for_garbage()
    {
        var svc = CreateService();

        svc.TryDecrypt("not base64 at all !@#$", out _).Should().BeFalse();
        svc.TryDecrypt("YWJj", out _).Should().BeFalse(); // base64 but too short
    }

    [Fact]
    public void IsEncrypted_returns_true_for_encrypted_value()
    {
        var svc = CreateService();
        var cipher = svc.Encrypt("data");

        svc.IsEncrypted(cipher).Should().BeTrue();
        svc.IsEncrypted("plain text").Should().BeFalse();
        svc.IsEncrypted(null).Should().BeFalse();
        svc.IsEncrypted(string.Empty).Should().BeFalse();
    }

    [Fact]
    public void ComputeBlindIndex_is_deterministic()
    {
        var svc = CreateService();

        var hash1 = svc.ComputeBlindIndex("john.doe@example.com");
        var hash2 = svc.ComputeBlindIndex("john.doe@example.com");

        hash1.Should().Be(hash2);
        hash1.Should().HaveLength(64); // SHA-256 hex
    }

    [Fact]
    public void ComputeBlindIndex_normalizes_case_and_whitespace()
    {
        var svc = CreateService();

        svc.ComputeBlindIndex("John.Doe@Example.com")
           .Should().Be(svc.ComputeBlindIndex("  john.doe@example.com  "));
    }

    [Fact]
    public void ComputeBlindIndex_different_keys_produce_different_hashes()
    {
        var svc1 = CreateService(passphrase: "passphrase-one-1111111111111111111111111");
        var svc2 = CreateService(passphrase: "passphrase-two-2222222222222222222222222");

        var h1 = svc1.ComputeBlindIndex("john@example.com");
        var h2 = svc2.ComputeBlindIndex("john@example.com");

        h1.Should().NotBe(h2);
    }

    [Fact]
    public void Constructor_throws_when_passphrase_too_short()
    {
        var config = new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Encryption:MasterPassphrase"] = "short",
                ["Encryption:KeySalt"]          = "salt",
            })
            .Build();

        Action act = () => new AesGcmEncryptionService(
            config, NullLogger<AesGcmEncryptionService>.Instance);

        act.Should().Throw<InvalidOperationException>()
           .WithMessage("*at least 16 characters*");
    }

    [Fact]
    public void Constructor_throws_when_passphrase_missing()
    {
        var config = new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Encryption:KeySalt"] = "salt",
            })
            .Build();

        Action act = () => new AesGcmEncryptionService(
            config, NullLogger<AesGcmEncryptionService>.Instance);

        act.Should().Throw<InvalidOperationException>()
           .WithMessage("*MasterPassphrase*");
    }

    [Fact]
    public void Encrypted_envelope_has_expected_structure()
    {
        var svc = CreateService();
        var cipher = svc.Encrypt("X"); // 1-byte plaintext

        var bytes = Convert.FromBase64String(cipher);

        bytes.Should().HaveCount(30);
        bytes[0].Should().Be(0x01); // version byte
    }
}
