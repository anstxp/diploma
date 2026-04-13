using HEMAX.Application.Common.Interfaces;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace HEMAX.Infrastructure.Persistence;

public class EncryptedStringConverter : ValueConverter<string, string>
{
    public EncryptedStringConverter(IEncryptionService encryption)
        : base(
            plaintext => Encrypt(encryption, plaintext),
            stored    => Decrypt(encryption, stored))
    { }

    private static string Encrypt(IEncryptionService enc, string plaintext)
        => enc.Encrypt(plaintext ?? string.Empty);

    private static string Decrypt(IEncryptionService enc, string stored)
    {
        if (enc.TryDecrypt(stored, out var plain))
            return plain;
        return stored ?? string.Empty;
    }
}

public class NullableEncryptedStringConverter : ValueConverter<string?, string?>
{
    public NullableEncryptedStringConverter(IEncryptionService encryption)
        : base(
            plaintext => EncryptNullable(encryption, plaintext),
            stored    => DecryptNullable(encryption, stored))
    { }

    private static string? EncryptNullable(IEncryptionService enc, string? plaintext)
        => plaintext == null ? null : enc.Encrypt(plaintext);

    private static string? DecryptNullable(IEncryptionService enc, string? stored)
    {
        if (stored == null) return null;
        if (enc.TryDecrypt(stored, out var plain))
            return plain;
        return stored;
    }
}
