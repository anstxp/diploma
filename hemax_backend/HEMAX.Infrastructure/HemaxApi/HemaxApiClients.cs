using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using HEMAX.Application.Common.Interfaces;
using Microsoft.Extensions.Logging;

namespace HEMAX.Infrastructure.HemaxApi;

public abstract class HemaxApiClientBase
{
    protected readonly HttpClient Http;
    protected readonly ILogger Logger;
    protected static readonly JsonSerializerOptions JsonOpts = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    protected HemaxApiClientBase(HttpClient http, ILogger logger)
    {
        Http = http;
        Logger = logger;
    }

    public async Task<bool> IsHealthyAsync(string healthPath, CancellationToken ct = default)
    {
        try
        {
            var resp = await Http.GetAsync(healthPath, ct);
            return resp.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            Logger.LogWarning(ex, "Health check failed for {BaseUrl}", Http.BaseAddress);
            return false;
        }
    }

    protected async Task<JsonElement> PostJsonAsync(
        string path, string payloadJson, CancellationToken ct)
    {
        using var content = new StringContent(payloadJson, Encoding.UTF8, "application/json");
        var resp = await Http.PostAsync(path, content, ct);

        var body = await resp.Content.ReadAsStringAsync(ct);

        if (!resp.IsSuccessStatusCode)
        {
            Logger.LogWarning("HEMAX API {Path} returned {Status}: {Body}",
                path, resp.StatusCode, body);

            if (resp.StatusCode == HttpStatusCode.UnprocessableEntity ||
                resp.StatusCode == HttpStatusCode.BadRequest)
                throw new HemaxApiValidationException(body);

            throw new HemaxApiException(
                $"HEMAX API call to {path} failed with {(int)resp.StatusCode}: {body}");
        }

        using var doc = JsonDocument.Parse(body);
        return doc.RootElement.Clone();
    }

    protected async Task<JsonElement> GetJsonAsync(string path, CancellationToken ct)
    {
        var resp = await Http.GetAsync(path, ct);
        var body = await resp.Content.ReadAsStringAsync(ct);

        if (!resp.IsSuccessStatusCode)
            throw new HemaxApiException($"HEMAX API call failed: {(int)resp.StatusCode}");

        using var doc = JsonDocument.Parse(body);
        return doc.RootElement.Clone();
    }

    protected static string InjectLang(string payloadJson, string? lang)
    {
        if (string.IsNullOrEmpty(lang)) return payloadJson;

        var node = JsonNode.Parse(payloadJson) as JsonObject
                   ?? throw new HemaxApiException(
                          "Cannot inject lang: payload is not a JSON object.");
        node["lang"] = lang;
        return node.ToJsonString();
    }
}


public class HemaxCbcClient : HemaxApiClientBase, IHemaxCbcClient
{
    public HemaxCbcClient(HttpClient http, ILogger<HemaxCbcClient> logger)
        : base(http, logger) { }

    public Task<bool> IsHealthyAsync(CancellationToken ct = default)
        => IsHealthyAsync("/health", ct);

    async Task<object> IHemaxCbcClient.AnalyzeAsync(object request, CancellationToken ct)
    {
        var json = request as string ?? JsonSerializer.Serialize(request, JsonOpts);
        return await PostJsonAsync("/analyze", json, ct);
    }

    async Task<object> IHemaxCbcClient.AnalyzeNarrativeAsync(object request, string? lang, CancellationToken ct)
    {
        var json = request as string ?? JsonSerializer.Serialize(request, JsonOpts);
        json = InjectLang(json, lang);
        return await PostJsonAsync("/analyze/narrative", json, ct);
    }
}


public class HemaxChemClient : HemaxApiClientBase, IHemaxChemClient
{
    public HemaxChemClient(HttpClient http, ILogger<HemaxChemClient> logger)
        : base(http, logger) { }

    public Task<bool> IsHealthyAsync(CancellationToken ct = default)
        => IsHealthyAsync("/chem/health", ct);

    async Task<object> IHemaxChemClient.AnalyzeAsync(object request, CancellationToken ct)
    {
        var json = request as string ?? JsonSerializer.Serialize(request, JsonOpts);
        return await PostJsonAsync("/chem/analyze", json, ct);
    }

    async Task<object> IHemaxChemClient.AnalyzeNarrativeAsync(object request, string? lang, CancellationToken ct)
    {
        var json = request as string ?? JsonSerializer.Serialize(request, JsonOpts);
        json = InjectLang(json, lang);
        return await PostJsonAsync("/chem/analyze/narrative", json, ct);
    }
}


public class HemaxRiskClient : HemaxApiClientBase, IHemaxRiskClient
{
    public HemaxRiskClient(HttpClient http, ILogger<HemaxRiskClient> logger)
        : base(http, logger) { }

    public Task<bool> IsHealthyAsync(CancellationToken ct = default)
        => IsHealthyAsync("/risk/healthz", ct);

    async Task<object> IHemaxRiskClient.AnalyzeAsync(object request, CancellationToken ct)
    {
        var json = request as string ?? JsonSerializer.Serialize(request, JsonOpts);
        return await PostJsonAsync("/risk/analyze", json, ct);
    }

    async Task<object> IHemaxRiskClient.AnalyzeNarrativeAsync(object request, string? lang, CancellationToken ct)
    {
        var json = request as string ?? JsonSerializer.Serialize(request, JsonOpts);
        json = InjectLang(json, lang);
        return await PostJsonAsync("/risk/analyze/narrative", json, ct);
    }
}


public class HemaxNeuroClient : HemaxApiClientBase, IHemaxNeuroClient
{
    public HemaxNeuroClient(HttpClient http, ILogger<HemaxNeuroClient> logger)
        : base(http, logger) { }

    public Task<bool> IsHealthyAsync(CancellationToken ct = default)
        => IsHealthyAsync("/neuro/healthz", ct);

    async Task<object> IHemaxNeuroClient.AnalyzeAsync(object request, CancellationToken ct)
    {
        var json = request as string ?? JsonSerializer.Serialize(request, JsonOpts);
        return await PostJsonAsync("/neuro/analyze", json, ct);
    }

    async Task<object> IHemaxNeuroClient.AnalyzeNarrativeAsync(object request, string? lang, CancellationToken ct)
    {
        var json = request as string ?? JsonSerializer.Serialize(request, JsonOpts);
        json = InjectLang(json, lang);
        return await PostJsonAsync("/neuro/analyze/narrative", json, ct);
    }
}


public class HemaxDermaClient : HemaxApiClientBase, IHemaxDermaClient
{
    public HemaxDermaClient(HttpClient http, ILogger<HemaxDermaClient> logger)
        : base(http, logger) { }

    public Task<bool> IsHealthyAsync(CancellationToken ct = default)
        => IsHealthyAsync("/derma/healthz", ct);

    public async Task<object> AnalyzeAsync(
        Stream imageStream, string fileName, string contentType,
        double? age = null, string? sex = null, string? localization = null,
        int topK = 3, CancellationToken ct = default)
    {
        using var content = new MultipartFormDataContent();

        var imageContent = new StreamContent(imageStream);
        imageContent.Headers.ContentType = new MediaTypeHeaderValue(contentType);
        content.Add(imageContent, "image", fileName);

        if (age.HasValue)
            content.Add(new StringContent(age.Value.ToString(System.Globalization.CultureInfo.InvariantCulture)), "age");
        if (!string.IsNullOrEmpty(sex))
            content.Add(new StringContent(sex), "sex");
        if (!string.IsNullOrEmpty(localization))
            content.Add(new StringContent(localization), "localization");
        content.Add(new StringContent(topK.ToString()), "top_k");

        var resp = await Http.PostAsync("/derma/analyze", content, ct);
        var body = await resp.Content.ReadAsStringAsync(ct);

        if (!resp.IsSuccessStatusCode)
        {
            Logger.LogWarning("DERMA returned {Status}: {Body}", resp.StatusCode, body);

            if (resp.StatusCode == HttpStatusCode.UnsupportedMediaType ||
                resp.StatusCode == HttpStatusCode.BadRequest ||
                resp.StatusCode == HttpStatusCode.UnprocessableEntity)
                throw new HemaxApiValidationException(body);

            throw new HemaxApiException($"DERMA failed: {(int)resp.StatusCode}: {body}");
        }

        using var doc = JsonDocument.Parse(body);
        return doc.RootElement.Clone();
    }
}


public class HemaxApiFacade : IHemaxApiFacade
{
    public IHemaxCbcClient   Cbc   { get; }
    public IHemaxChemClient  Chem  { get; }
    public IHemaxRiskClient  Risk  { get; }
    public IHemaxNeuroClient Neuro { get; }
    public IHemaxDermaClient Derma { get; }

    public HemaxApiFacade(
        IHemaxCbcClient cbc, IHemaxChemClient chem, IHemaxRiskClient risk,
        IHemaxNeuroClient neuro, IHemaxDermaClient derma)
    {
        Cbc = cbc; Chem = chem; Risk = risk; Neuro = neuro; Derma = derma;
    }
}


public class HemaxApiException : Exception
{
    public HemaxApiException(string message) : base(message) { }
}

public class HemaxApiValidationException : HemaxApiException
{
    public string ResponseBody { get; }
    public HemaxApiValidationException(string body)
        : base("HEMAX API rejected request") => ResponseBody = body;
}
