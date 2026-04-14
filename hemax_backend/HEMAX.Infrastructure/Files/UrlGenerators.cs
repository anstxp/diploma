using Azure.Storage.Blobs;
using Azure.Storage.Sas;
using HEMAX.Application.Common.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace HEMAX.Infrastructure.Files;

public class LocalDiskUrlGenerator : IFileUrlGenerator
{
    private readonly string _publicBaseUrl;

    public LocalDiskUrlGenerator(IConfiguration config)
    {
        _publicBaseUrl = config["FileStorage:PublicBaseUrl"] ?? "/files";
    }

    public string GetDownloadUrl(string storageKey)
    {
        return $"{_publicBaseUrl.TrimEnd('/')}/{storageKey}";
    }
}

public class AzureBlobUrlGenerator : IFileUrlGenerator
{
    private readonly BlobContainerClient _container;
    private readonly int _sasExpiryHours;
    private readonly ILogger<AzureBlobUrlGenerator> _logger;

    public AzureBlobUrlGenerator(IConfiguration config, ILogger<AzureBlobUrlGenerator> logger)
    {
        _logger = logger;
        var conn = config["FileStorage:AzureBlob:ConnectionString"]
            ?? throw new InvalidOperationException("FileStorage:AzureBlob:ConnectionString is missing");
        var containerName = config["FileStorage:AzureBlob:ContainerName"] ?? "hemax-files";
        var sasExpiryStr = config["FileStorage:AzureBlob:SasExpiryHours"];
        _sasExpiryHours = int.TryParse(sasExpiryStr, out var h) ? h : 1;

        var serviceClient = new BlobServiceClient(conn);
        _container = serviceClient.GetBlobContainerClient(containerName);
    }

    public string GetDownloadUrl(string storageKey)
    {
        var blobClient = _container.GetBlobClient(storageKey);
        if (!blobClient.CanGenerateSasUri)
        {
            _logger.LogWarning("Cannot generate SAS — returning bare URI");
            return blobClient.Uri.ToString();
        }

        var sasBuilder = new BlobSasBuilder
        {
            BlobContainerName = blobClient.BlobContainerName,
            BlobName = blobClient.Name,
            Resource = "b",
            ExpiresOn = DateTimeOffset.UtcNow.AddHours(_sasExpiryHours),
        };
        sasBuilder.SetPermissions(BlobSasPermissions.Read);
        return blobClient.GenerateSasUri(sasBuilder).ToString();
    }
}
