using HEMAX.Application.Users;
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

    [HttpGet]
    public async Task<ActionResult<UserProfileDto>> GetMine(CancellationToken ct)
    {
        return Ok(await _mediator.Send(new GetMyProfileQuery(), ct));
    }

    [HttpGet("{userId:guid}")]
    public async Task<ActionResult<UserProfileDto>> GetByUserId(
        Guid userId, CancellationToken ct)
    {
        return Ok(await _mediator.Send(new GetUserProfileQuery(userId), ct));
    }

    [HttpPut]
    public async Task<ActionResult<UserProfileDto>> UpdateMine(
        [FromBody] UpdateProfileRequest body,
        CancellationToken ct)
    {
        return Ok(await _mediator.Send(new UpdateMyProfileCommand(body), ct));
    }

    [HttpDelete]
    public async Task<IActionResult> DeleteMine(CancellationToken ct)
    {
        await _mediator.Send(new DeleteAccountCommand(), ct);
        return NoContent();
    }
}
