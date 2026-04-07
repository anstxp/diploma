using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Enums;

namespace HEMAX.Application.Analyses.Clients;

public interface IHemaxAnalysisClient
{
    AnalysisType Type { get; }

    Task<object> AnalyzeAsync(string payloadJson, string? language, CancellationToken ct);
}

public interface IHemaxAnalysisClientRegistry
{
    IHemaxAnalysisClient For(AnalysisType type);
}

internal sealed class HemaxAnalysisClientRegistry : IHemaxAnalysisClientRegistry
{
    private readonly Dictionary<AnalysisType, IHemaxAnalysisClient> _byType;

    public HemaxAnalysisClientRegistry(IEnumerable<IHemaxAnalysisClient> clients)
    {
        _byType = clients.ToDictionary(c => c.Type);
    }

    public IHemaxAnalysisClient For(AnalysisType type)
    {
        if (_byType.TryGetValue(type, out var client))
            return client;
        throw new InvalidOperationException(
            $"No HEMAX analysis client registered for {type}. " +
            "Did you forget to register an adapter in DependencyInjection?");
    }
}
