using HEMAX.Application.BlogPosts;
using HEMAX.Application.Common.Models;
using HEMAX.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace HEMAX.Web.Controllers;

[ApiController]
[Route("api/blog")]
public class BlogController : ControllerBase
{
    private readonly IMediator _mediator;
    public BlogController(IMediator mediator) => _mediator = mediator;

    /// <summary>Public feed.</summary>
    [HttpGet]
    [AllowAnonymous]
    public async Task<ActionResult<PagedResult<BlogPostListItemDto>>> GetFeed(
        [FromQuery] string? tag,
        [FromQuery] string? search,
        [FromQuery] Guid? authorId,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        CancellationToken ct = default)
    {
        var query = new GetBlogFeedQuery(tag, search, authorId,
            new PageRequest { Page = page, PageSize = pageSize });
        return Ok(await _mediator.Send(query, ct));
    }

    [HttpGet("{id:guid}")]
    [AllowAnonymous]
    public async Task<ActionResult<BlogPostDto>> GetById(Guid id, CancellationToken ct)
        => Ok(await _mediator.Send(new GetBlogPostByIdQuery(id), ct));

    [Authorize]
    [HttpPost]
    public async Task<ActionResult<Guid>> Create(
        [FromBody] CreateBlogPostCommand cmd, CancellationToken ct)
    {
        var id = await _mediator.Send(cmd, ct);
        return CreatedAtAction(nameof(GetById), new { id }, new { id });
    }

    [Authorize]
    [HttpPut("{id:guid}")]
    public async Task<IActionResult> Update(
        Guid id, [FromBody] UpdateBlogPostBody body, CancellationToken ct)
    {
        await _mediator.Send(new UpdateBlogPostCommand(id, body.Title, body.Content, body.Tags), ct);
        return NoContent();
    }

    [Authorize]
    [HttpDelete("{id:guid}")]
    public async Task<IActionResult> Delete(Guid id, CancellationToken ct)
    {
        await _mediator.Send(new DeleteBlogPostCommand(id), ct);
        return NoContent();
    }

    [Authorize]
    [HttpPost("{id:guid}/cover")]
    [RequestSizeLimit(10 * 1024 * 1024)]
    public async Task<ActionResult<string>> UploadCover(
        Guid id, IFormFile image, CancellationToken ct)
    {
        if (image is null) return BadRequest(new { error = "Image file required" });

        await using var stream = image.OpenReadStream();
        var url = await _mediator.Send(
            new UploadBlogCoverCommand(id, stream, image.FileName, image.ContentType), ct);
        return Ok(new { url });
    }

    [Authorize]
    [HttpDelete("{id:guid}/cover")]
    public async Task<IActionResult> RemoveCover(Guid id, CancellationToken ct)
    {
        await _mediator.Send(new RemoveBlogCoverCommand(id), ct);
        return NoContent();
    }

    [Authorize(Roles = Roles.Administrator)]
    [HttpPost("{id:guid}/recover")]
    public async Task<IActionResult> Recover(Guid id, CancellationToken ct)
    {
        await _mediator.Send(new RecoverBlogPostCommand(id), ct);
        return NoContent();
    }

    [Authorize]
    [HttpPost("{id:guid}/like")]
    public async Task<ActionResult<bool>> Like(Guid id, CancellationToken ct)
    {
        var liked = await _mediator.Send(new ToggleLikeCommand(id), ct);
        return Ok(new { liked });
    }


    [HttpGet("{id:guid}/comments")]
    [AllowAnonymous]
    public async Task<ActionResult<PagedResult<CommentDto>>> GetComments(
        Guid id,
        [FromQuery] int page = 1, [FromQuery] int pageSize = 50,
        CancellationToken ct = default)
        => Ok(await _mediator.Send(
            new GetCommentsQuery(id, new PageRequest { Page = page, PageSize = pageSize }), ct));

    [Authorize]
    [HttpPost("{id:guid}/comments")]
    public async Task<ActionResult<CommentDto>> AddComment(
        Guid id, [FromBody] AddCommentBody body, CancellationToken ct)
    {
        var dto = await _mediator.Send(new CreateCommentCommand(id, body.Content), ct);
        return Ok(dto);
    }

    [Authorize]
    [HttpDelete("comments/{commentId:guid}")]
    public async Task<IActionResult> DeleteComment(Guid commentId, CancellationToken ct)
    {
        await _mediator.Send(new DeleteCommentCommand(commentId), ct);
        return NoContent();
    }


    [Authorize(Roles = Roles.Administrator)]
    [HttpGet("deleted")]
    public async Task<ActionResult<PagedResult<BlogPostListItemDto>>> GetDeleted(
        [FromQuery] int page = 1, [FromQuery] int pageSize = 50,
        CancellationToken ct = default)
        => Ok(await _mediator.Send(
            new GetDeletedPostsQuery(new PageRequest { Page = page, PageSize = pageSize }), ct));
}

public record UpdateBlogPostBody(string Title, string Content, IReadOnlyList<string>? Tags);
public record AddCommentBody(string Content);
