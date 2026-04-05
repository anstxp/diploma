namespace HEMAX.Application.Common.Interfaces;

public interface IEncryptionService
{
    string Encrypt(string plaintext);

    string Decrypt(string ciphertext);

    bool TryDecrypt(string ciphertext, out string plaintext);

    bool IsEncrypted(string? value);

    string ComputeBlindIndex(string value);
}
