using HEMAX.Application.Common.Interfaces;

namespace HEMAX.Infrastructure.Files;

public interface IFileUrlGenerator
{
    string GetDownloadUrl(string storageKey);
}
