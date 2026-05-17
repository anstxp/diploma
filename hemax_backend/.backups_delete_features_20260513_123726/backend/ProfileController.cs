using HEMAX.Application.UserProfiles;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace HEMAX.Web.Controllers;

[ApiController]
[Authorize]
[Route("api/profile")]
public class ProfileController : ControllerBase
{
    private readonly IMediator _mediator;
    public ProfileController(IMediator mediator) => _mediator = mediator;

    /// <summary>Get the current user's profile (auto-creates if missing).</summary>
    [HttpGet]
    public async Task<ActionResult<UserProfileDto>> GetMine(CancellationToken ct)
    {
        return Ok(await _mediator.Send(new GetMyProfileQuery(), ct));
    }

    /// <summary>
    /// Get another user's full medical profile.
    /// Allowed for: the user themselves, an Accepted-linked Doctor, or an Administrator.
    /// </summary>
    [HttpGet("{userId:guid}")]
    public async Task<ActionResult<UserProfileDto>> GetByUserId(
        Guid userId, CancellationToken ct)
    {
        return Ok(await _mediator.Send(new GetUserProfileQuery(userId), ct));
    }

    /// <summary>Update the current user's profile (partial — only non-null fields).</summary>
    [HttpPut]
    public async Task<ActionResult<UserProfileDto>> UpdateMine(
        [FromBody] UpdateProfileRequest body,
        CancellationToken ct)
    {
        return Ok(await _mediator.Send(new UpdateMyProfileCommand(body), ct));
    }
}
