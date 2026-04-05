
namespace HEMAX.Infrastructure.Files;

public interface IFileSignatureValidator
{
    Task ValidateAsync(Stream data, string declaredContentType,
                       FileKind kind, long maxBytes = 0,
                       CancellationToken ct = default);
}

public enum FileKind
{
    /// <summary>JPEG, PNG, or WebP.</summary>
    Image,
    /// <summary>PDF.</summary>
    Pdf,
}

public class InvalidFileException : Exception
{
    public InvalidFileException(string message) : base(message) { }
}
