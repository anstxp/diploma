using Azure.Storage.Blobs;
using Azure.Storage.Blobs.Models;
using Azure.Storage.Sas;
using HEMAX.Application.Common.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace HEMAX.Infrastructure.Files;

public class AzureBlobFileStorage : IFileStorageService
{
    private readonly BlobContainerClient _container;
    private readonly ILogger<AzureBlobFileStorage> _logger;
    private readonly int _sasExpiryHours;
    private readonly string _accountName;

    public AzureBlobFileStorage(
        IConfiguration config,
        ILogger<AzureBlobFileStorage> logger)
    {
        _logger = logger;

        var conn = config["FileStorage:AzureBlob:ConnectionString"]
            ?? throw new InvalidOperationException(
                "FileStorage:AzureBlob:ConnectionString is missing. " +
                "Get it from Azure Portal > Storage Account > Access keys.");

        var containerName = config["FileStorage:AzureBlob:ContainerName"] ?? "hemax-files";

        var sasExpiryStr = config["FileStorage:AzureBlob:SasExpiryHours"];
        _sasExpiryHours = int.TryParse(sasExpiryStr, out var h) ? h : 1;

        var serviceClient = new BlobServiceClient(conn);
        _accountName = serviceClient.AccountName;
        _container = serviceClient.GetBlobContainerClient(containerName);

        _container.CreateIfNotExists(PublicAccessType.None);

        _logger.LogInformation(
            "Azure Blob Storage initialized: account={Account}, container={Container}, sasExpiryHours={Hours}",
            _accountName, containerName, _sasExpiryHours);
    }

    public async Task<(string StorageKey, string? PublicUrl)> SaveAsync(
        Stream content, string fileName, string contentType, CancellationToken ct,
        string? category = null)
    {
        var folder = string.IsNullOrWhiteSpace(category)
            ? "misc"
            : SanitizeCategory(category);

        var now = DateTime.UtcNow;
        var safeName = MakeSafeFileName(fileName);
        var storageKey = $"{folder}/{now:yyyy}/{now:MM}/{now:dd}/{Guid.NewGuid():N}_{safeName}";

        var blobClient = _container.GetBlobClient(storageKey);

        var headers = new BlobHttpHeaders { ContentType = contentType };
        await blobClient.UploadAsync(
            content,
            new BlobUploadOptions { HttpHeaders = headers },
            ct);

        var sasUrl = GenerateReadSasUrl(blobClient);

        _logger.LogInformation(
            "Uploaded blob: key={Key}, size={Size}",
            storageKey, content.Length);

        return (storageKey, sasUrl);
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

    public async Task<Stream> OpenReadAsync(string storageKey, CancellationToken ct)
    {
        var blobClient = _container.GetBlobClient(storageKey);
        if (!await blobClient.ExistsAsync(ct))
            throw new FileNotFoundException("Blob not found", storageKey);

        var response = await blobClient.DownloadStreamingAsync(cancellationToken: ct);
        return response.Value.Content;
    }

    public async Task DeleteAsync(string storageKey, CancellationToken ct)
    {
        var blobClient = _container.GetBlobClient(storageKey);
        await blobClient.DeleteIfExistsAsync(cancellationToken: ct);
        _logger.LogInformation("Deleted blob: key={Key}", storageKey);
    }

    private string GenerateReadSasUrl(BlobClient blobClient)
    {
        if (!blobClient.CanGenerateSasUri)
        {
            _logger.LogWarning("BlobClient cannot generate SAS — returning blob URI without token");
            return blobClient.Uri.ToString();
        }

        var sasBuilder = new BlobSasBuilder
        {
            BlobContainerName = blobClient.BlobContainerName,
            BlobName = blobClient.Name,
            Resource = "b", // blob
            ExpiresOn = DateTimeOffset.UtcNow.AddHours(_sasExpiryHours),
        };
        sasBuilder.SetPermissions(BlobSasPermissions.Read);

        return blobClient.GenerateSasUri(sasBuilder).ToString();
    }

    private static string MakeSafeFileName(string name)
    {
        var invalid = Path.GetInvalidFileNameChars();
        var safe = string.Concat(name.Where(c => !invalid.Contains(c) && c != '/' && c != '\\'));
        if (string.IsNullOrWhiteSpace(safe)) safe = "file";
        if (safe.Length > 100) safe = safe.Substring(0, 100);
        return safe;
    }
}
