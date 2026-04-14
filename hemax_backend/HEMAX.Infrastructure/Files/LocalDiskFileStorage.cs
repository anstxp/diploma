using HEMAX.Application.Common.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace HEMAX.Infrastructure.Files;

public class LocalDiskFileStorage : IFileStorageService
{
    private readonly string _root;
    private readonly string _publicBaseUrl;
    private readonly ILogger<LocalDiskFileStorage> _logger;

    public LocalDiskFileStorage(IConfiguration config, ILogger<LocalDiskFileStorage> logger)
    {
        _root = Path.GetFullPath(config["FileStorage:Root"] ?? "./uploads");
        _publicBaseUrl = config["FileStorage:PublicBaseUrl"] ?? "/files";
        _logger = logger;

        Directory.CreateDirectory(_root);
    }

    public async Task<(string StorageKey, string? PublicUrl)> SaveAsync(
        Stream content, string fileName, string contentType, CancellationToken ct,
        string? category = null)
    {
        var folder = string.IsNullOrWhiteSpace(category) ? "misc" : SanitizeCategory(category);
        var now = DateTime.UtcNow;
        var subDir = Path.Combine(folder, now.ToString("yyyy"), now.ToString("MM"), now.ToString("dd"));
        var fullDir = Path.Combine(_root, subDir);
        Directory.CreateDirectory(fullDir);

        var safeName = MakeSafeFileName(fileName);
        var storageKey = Path.Combine(subDir, $"{Guid.NewGuid():N}_{safeName}")
                            .Replace('\\', '/');
        var fullPath   = Path.Combine(_root, storageKey);

        await using var fs = File.Create(fullPath);
        await content.CopyToAsync(fs, ct);

        var publicUrl = $"{_publicBaseUrl.TrimEnd('/')}/{storageKey}";
        _logger.LogInformation("Saved file to {Path}", fullPath);
        return (storageKey, publicUrl);
    }

    public Task<Stream> OpenReadAsync(string storageKey, CancellationToken ct)
    {
        var fullPath = Path.Combine(_root, storageKey);
        if (!File.Exists(fullPath))
            throw new FileNotFoundException("File not found", storageKey);

        Stream s = File.OpenRead(fullPath);
        return Task.FromResult(s);
    }

    public Task DeleteAsync(string storageKey, CancellationToken ct)
    {
        var fullPath = Path.Combine(_root, storageKey);
        if (File.Exists(fullPath))
            File.Delete(fullPath);
        return Task.CompletedTask;
    }

    private static string MakeSafeFileName(string name)
    {
        var invalid = Path.GetInvalidFileNameChars();
        var safe = string.Concat(name.Where(c => !invalid.Contains(c)));
        if (string.IsNullOrWhiteSpace(safe)) safe = "file";
        if (safe.Length > 100) safe = safe.Substring(0, 100);
        return safe;
    }

    private static string SanitizeCategory(string category)
    {
        var lower = category.ToLowerInvariant();
        var safe = new string(lower
            .Select(c => char.IsLetterOrDigit(c) || c == '-' ? c : '-')
            .ToArray())
            .Trim('-');
        return string.IsNullOrEmpty(safe) ? "misc" : safe;
    }
}
