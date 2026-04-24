using System.Net;
using System.Text.Json;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Domain.Exceptions;
using HEMAX.Infrastructure.Files;
using HEMAX.Infrastructure.HemaxApi;

namespace HEMAX.Web.Middleware;

public class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;

    public ExceptionHandlingMiddleware(RequestDelegate next,
        ILogger<ExceptionHandlingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext ctx)
    {
        try
        {
            await _next(ctx);
        }
        catch (Exception ex)
        {
            await HandleAsync(ctx, ex);
        }
    }

    private async Task HandleAsync(HttpContext ctx, Exception ex)
    {
        var (statusCode, payload) = ex switch
        {
            ValidationException v => (
                HttpStatusCode.UnprocessableEntity,
                (object)new
                {
                    type   = "validation_error",
                    title  = "One or more validation errors occurred",
                    status = 422,
                    errors = v.Errors,
                }),

            UnauthorizedException u => (
                HttpStatusCode.Unauthorized,
                new { type = "unauthorized", title = u.Message, status = 401 }),

            ForbiddenException f => (
                HttpStatusCode.Forbidden,
                new { type = "forbidden", title = f.Message, status = 403 }),

            ForbiddenAccessException fa => (
                HttpStatusCode.Forbidden,
                new { type = "forbidden", title = fa.Message, status = 403 }),

            EntityNotFoundException nf => (
                HttpStatusCode.NotFound,
                new { type = "not_found", title = nf.Message,
                      status = 404, entity = nf.EntityName, key = nf.Key.ToString() }),

            DuplicateEntityException d => (
                HttpStatusCode.Conflict,
                new { type = "duplicate", title = d.Message, status = 409 }),

            BusinessRuleViolationException b => (
                HttpStatusCode.BadRequest,
                new { type = "business_rule", title = b.Message, status = 400, code = b.Code }),

            InvalidFileException invf => (
                HttpStatusCode.BadRequest,
                new { type = "invalid_file", title = invf.Message, status = 400, code = "INVALID_FILE" }),

            HemaxApiValidationException hv => (
                HttpStatusCode.BadRequest,
                new { type = "hemax_api_validation", title = "HEMAX engine rejected input",
                      status = 400, body = hv.ResponseBody }),

            HemaxApiException he => (
                HttpStatusCode.BadGateway,
                new { type = "hemax_api_error", title = he.Message, status = 502 }),

            _ => (
                HttpStatusCode.InternalServerError,
                new { type = "internal_error", title = "An unexpected error occurred",
                      status = 500 })
        };

        if (statusCode == HttpStatusCode.InternalServerError)
            _logger.LogError(ex, "Unhandled exception");
        else
            _logger.LogWarning("Handled {Type}: {Message}", ex.GetType().Name, ex.Message);

        ctx.Response.ContentType = "application/problem+json";
        ctx.Response.StatusCode  = (int)statusCode;
        await ctx.Response.WriteAsJsonAsync(payload);
    }
}
