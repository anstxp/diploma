using System.Reflection;
using FluentValidation;
using HEMAX.Application.Analyses.Clients;
using HEMAX.Application.Analyses.Context;
using HEMAX.Application.Analyses.Severity;
using HEMAX.Application.Common.Behaviors;
using MediatR;
using Microsoft.Extensions.DependencyInjection;

namespace HEMAX.Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        var assembly = Assembly.GetExecutingAssembly();

        services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssembly(assembly);
            cfg.AddOpenBehavior(typeof(LoggingBehavior<,>));
            cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
        });

        services.AddValidatorsFromAssembly(assembly);

        services.AddAutoMapper(cfg => cfg.AddMaps(assembly));

        services.AddScoped<ISeverityExtractor, CbcSeverityExtractor>();
        services.AddScoped<ISeverityExtractor, ChemSeverityExtractor>();
        services.AddScoped<ISeverityExtractor, RiskSeverityExtractor>();
        services.AddScoped<ISeverityExtractor, NeuroSeverityExtractor>();
        services.AddScoped<ISeverityExtractor, DermaSeverityExtractor>();
        services.AddScoped<ISeverityExtractorRegistry, SeverityExtractorRegistry>();

        services.AddScoped<IHemaxAnalysisClient, CbcAnalysisClient>();
        services.AddScoped<IHemaxAnalysisClient, ChemAnalysisClient>();
        services.AddScoped<IHemaxAnalysisClient, RiskAnalysisClient>();
        services.AddScoped<IHemaxAnalysisClient, NeuroAnalysisClient>();
        services.AddScoped<IHemaxAnalysisClientRegistry, HemaxAnalysisClientRegistry>();

        services.AddScoped<IPatientContextBuilder, PatientContextBuilder>();
        services.AddScoped<IRecentLabsMerger, RecentLabsMerger>();

        return services;
    }
}
