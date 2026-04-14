namespace HEMAX.Infrastructure.Files;

public sealed class FileSignatureValidator : IFileSignatureValidator
{
    private static readonly HashSet<string> ImageMimes = new(StringComparer.OrdinalIgnoreCase)
        { "image/jpeg", "image/jpg", "image/png", "image/webp" };

    public async Task ValidateAsync(Stream data, string declaredContentType,
                                     FileKind kind, long maxBytes = 0,
                                     CancellationToken ct = default)
    {
        if (data is null)
            throw new InvalidFileException("Empty upload.");

        if (data.CanSeek)
        {
            if (data.Length == 0)
                throw new InvalidFileException("Empty upload.");
            if (maxBytes > 0 && data.Length > maxBytes)
                throw new InvalidFileException(
                    $"Файл завеликий — максимум {maxBytes / (1024 * 1024)} МБ.");
        }

        if (!data.CanSeek)
            throw new InvalidFileException("File stream must be seekable for validation.");

        var origin = data.Position;
        var head = new byte[16];
        int n = 0;
        while (n < head.Length)
        {
            var r = await data.ReadAsync(head.AsMemory(n, head.Length - n), ct);
            if (r == 0) break;
            n += r;
        }
        data.Position = origin;

        if (n < 4)
            throw new InvalidFileException("Файл пошкоджено (надто короткий).");

        switch (kind)
        {
            case FileKind.Image:
                ValidateImage(head, n, declaredContentType);
                break;
            case FileKind.Pdf:
                ValidatePdf(head, n, declaredContentType);
                break;
            default:
                throw new ArgumentOutOfRangeException(nameof(kind));
        }
    }

    private static void ValidateImage(byte[] head, int n, string declaredContentType)
    {
        if (!ImageMimes.Contains(declaredContentType))
            throw new InvalidFileException(
                $"Дозволені формати зображень: JPEG, PNG, WebP. Отримано: {declaredContentType}.");

        // JPEG: FF D8 FF
        bool isJpeg = n >= 3 && head[0] == 0xFF && head[1] == 0xD8 && head[2] == 0xFF;

        // PNG: 89 50 4E 47 0D 0A 1A 0A
        bool isPng = n >= 8
            && head[0] == 0x89 && head[1] == 0x50 && head[2] == 0x4E && head[3] == 0x47
            && head[4] == 0x0D && head[5] == 0x0A && head[6] == 0x1A && head[7] == 0x0A;

        // WebP: "RIFF" .... "WEBP"
        bool isWebp = n >= 12
            && head[0] == 0x52 && head[1] == 0x49 && head[2] == 0x46 && head[3] == 0x46  // RIFF
            && head[8] == 0x57 && head[9] == 0x45 && head[10] == 0x42 && head[11] == 0x50; // WEBP

        if (!(isJpeg || isPng || isWebp))
            throw new InvalidFileException(
                "Файл не є дійсним зображенням JPEG/PNG/WebP. Можливо, ви завантажили інший формат.");

        if (isJpeg && !(declaredContentType.Equals("image/jpeg", StringComparison.OrdinalIgnoreCase)
                        || declaredContentType.Equals("image/jpg", StringComparison.OrdinalIgnoreCase)))
            throw new InvalidFileException("Заявлений тип не співпадає з фактичним JPEG-зображенням.");
        if (isPng && !declaredContentType.Equals("image/png", StringComparison.OrdinalIgnoreCase))
            throw new InvalidFileException("Заявлений тип не співпадає з фактичним PNG-зображенням.");
        if (isWebp && !declaredContentType.Equals("image/webp", StringComparison.OrdinalIgnoreCase))
            throw new InvalidFileException("Заявлений тип не співпадає з фактичним WebP-зображенням.");
    }

    private static void ValidatePdf(byte[] head, int n, string declaredContentType)
    {
        if (!declaredContentType.Equals("application/pdf", StringComparison.OrdinalIgnoreCase))
            throw new InvalidFileException(
                $"Очікується PDF (application/pdf). Отримано: {declaredContentType}.");

        // PDF: 25 50 44 46 2D ("%PDF-")
        bool isPdf = n >= 5
            && head[0] == 0x25 && head[1] == 0x50 && head[2] == 0x44 && head[3] == 0x46 && head[4] == 0x2D;

        if (!isPdf)
            throw new InvalidFileException(
                "Файл не є дійсним PDF (відсутня сигнатура %PDF-).");
    }
}
