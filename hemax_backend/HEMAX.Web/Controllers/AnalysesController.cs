using HEMAX.Application.Analyses;
using HEMAX.Application.Common.Models;
using HEMAX.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace HEMAX.Web.Controllers;

[ApiController]
[Route("api/analyses")]
[Authorize]
public class AnalysesController : ControllerBase
{
    private readonly IMediator _mediator;
    public AnalysesController(IMediator mediator) => _mediator = mediator;

    [HttpGet]
    public async Task<ActionResult<PagedResult<AnalysisDto>>> GetHistory(
        [FromQuery] Guid? userId,
        [FromQuery] AnalysisType? type,
        [FromQuery] AnalysisSeverity? minSeverity,
        [FromQuery] DateTimeOffset? from,
        [FromQuery] DateTimeOffset? to,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        CancellationToken ct = default)
    {
        var query = new GetAnalysisHistoryQuery(
            userId, type, minSeverity, from, to,
            new PageRequest { Page = page, PageSize = pageSize });
        return Ok(await _mediator.Send(query, ct));
    }

    [HttpGet("{id:guid}")]
    public async Task<ActionResult<AnalysisDetailDto>> GetById(
        Guid id,
        [FromQuery] string? lang,
        CancellationToken ct)
        => Ok(await _mediator.Send(new GetAnalysisByIdQuery(id, lang), ct));

    [HttpPost("{type}")]
    public async Task<ActionResult<AnalysisDto>> Submit(
        AnalysisType type,
        [FromBody] SubmitAnalysisRequest body,
        [FromQuery] string? lang,
        [FromQuery] bool mergeRecentLabs,
        CancellationToken ct)
    {
        var cmd = new SubmitAnalysisCommand(type, body.PayloadJson, lang, mergeRecentLabs);
        return Ok(await _mediator.Send(cmd, ct));
    }

    [HttpPost("derma")]
    // Bug fix May 2026: was 15MB at the controller layer but the handler's
    // MaxDermaImageBytes constant is 10MB and the frontend validation cap
    // is also 10MB. Align all three so the rejection message is consistent
    // and the request doesn't get bounced at a different layer than the
    // user expects. 10MB is the canonical value.
    [RequestSizeLimit(10 * 1024 * 1024)]
    public async Task<ActionResult<AnalysisDto>> SubmitDerma(
        IFormFile image,
        [FromForm] double? age,
        [FromForm] string? sex,
        [FromForm] string? localization,
        [FromForm] int topK = 3,
        // Bug fix May 2026: accept `language` from FormData. Previously
        // the frontend's derma-form.vue appended it but no controller
        // parameter received it, so it was discarded by ASP.NET model
        // binding before the command was even built.
        [FromForm] string? language = null,
        CancellationToken ct = default)
    {
        if (image is null) return BadRequest(new { error = "Image required" });

        await using var stream = image.OpenReadStream();
        var cmd = new SubmitDermaAnalysisCommand(
            stream, image.FileName, image.ContentType,
            age, sex, localization, topK, language);
        return Ok(await _mediator.Send(cmd, ct));
    }

    [HttpPost("pdf/extract")]
    [RequestSizeLimit(20 * 1024 * 1024)]
    public async Task<ActionResult<PdfExtractionDto>> ExtractFromPdf(
        IFormFile pdf,
        [FromQuery] string? hint,
        CancellationToken ct = default)
    {
        if (pdf is null) return BadRequest(new { error = "PDF required" });
        if (pdf.ContentType != "application/pdf")
            return BadRequest(new { error = "File must be application/pdf" });

        await using var stream = pdf.OpenReadStream();
        var cmd = new ExtractFromPdfCommand(stream, pdf.FileName, pdf.ContentType, hint);
        return Ok(await _mediator.Send(cmd, ct));
    }

    [HttpPost("pdf/submit")]
    public async Task<ActionResult<AnalysisDto>> SubmitFromPdf(
        [FromBody] SubmitFromPdfRequest body,
        [FromQuery] string? lang,
        CancellationToken ct = default)
    {
        var cmd = new SubmitAnalysisFromPdfCommand(
            body.Type, body.PayloadJson, lang, body.PdfFileAssetId);
        return Ok(await _mediator.Send(cmd, ct));
    }

    [HttpGet("timeline")]
    public async Task<ActionResult<IReadOnlyList<TimelinePoint>>> GetTimeline(
        [FromQuery] AnalysisType type,
        [FromQuery] string field,
        [FromQuery] Guid? userId,
        [FromQuery] DateTimeOffset? from,
        [FromQuery] DateTimeOffset? to,
        CancellationToken ct)
    {
        var query = new GetHealthTimelineQuery(userId, type, field, from, to);
        return Ok(await _mediator.Send(query, ct));
    }

    [HttpGet("compare")]
    public async Task<ActionResult<AnalysisComparisonDto>> Compare(
        [FromQuery] Guid olderId, [FromQuery] Guid newerId, CancellationToken ct)
        => Ok(await _mediator.Send(new CompareAnalysesQuery(olderId, newerId), ct));

    /// <summary>Doctor adds note to a patient's analysis.</summary>
    [Authorize(Roles = $"{Roles.Doctor},{Roles.Administrator}")]
    [HttpPatch("{id:guid}/annotate")]
    public async Task<ActionResult<AnalysisDto>> Annotate(
        Guid id, [FromBody] AnnotateRequest body, CancellationToken ct)
        => Ok(await _mediator.Send(new AnnotateAnalysisCommand(id, body.Note), ct));

    [HttpDelete("{id:guid}")]
    public async Task<IActionResult> Delete(Guid id, CancellationToken ct)
    {
        await _mediator.Send(new DeleteAnalysisCommand(id), ct);
        return NoContent();
    }
}

public record SubmitAnalysisRequest(string PayloadJson);
public record AnnotateRequest(string Note);
public record SubmitFromPdfRequest(AnalysisType Type, string PayloadJson, Guid PdfFileAssetId);
