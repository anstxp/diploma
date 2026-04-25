using HEMAX.Application.Auth;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;

namespace HEMAX.Web.Controllers;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly IMediator _mediator;
    public AuthController(IMediator mediator) => _mediator = mediator;

    // Bug fix May 2026: actually apply the strict AuthPolicy rate limiter
    // (10 req/min/IP — declared in Program.cs but previously never wired
    // to any endpoint). The brute-force-attractive endpoints — login,
    // register, refresh, change-password — each get the limiter so they
    // can't be hammered by a credential-stuffing or token-grinding client.
    //
    // We intentionally DON'T limit /logout, /verify, /me — they're either
    // harmless or already require a valid bearer token (so they're under
    // the global 100/min limiter and that's enough).

    [HttpPost("register")]
    [EnableRateLimiting("AuthPolicy")]
    public async Task<IActionResult> Register(
        [FromBody] RegisterCommand cmd, CancellationToken ct)
    {
        var userId = await _mediator.Send(cmd, ct);
        return CreatedAtAction(nameof(GetMe), new { }, new { userId });
    }

    [HttpPost("login")]
    [EnableRateLimiting("AuthPolicy")]
    public async Task<ActionResult<AuthTokensDto>> Login(
        [FromBody] LoginCommand cmd, CancellationToken ct)
        => Ok(await _mediator.Send(cmd, ct));

    [HttpPost("refresh")]
    [EnableRateLimiting("AuthPolicy")]
    public async Task<ActionResult<AuthTokensDto>> Refresh(
        [FromBody] RefreshTokensCommand cmd, CancellationToken ct)
        => Ok(await _mediator.Send(cmd, ct));

    [Authorize]
    [HttpPost("logout")]
    public async Task<IActionResult> Logout(
        [FromBody] LogoutCommand cmd, CancellationToken ct)
    {
        await _mediator.Send(cmd, ct);
        return NoContent();
    }

    [HttpGet("verify")]
    public async Task<IActionResult> VerifyEmail(
        [FromQuery] Guid userId, [FromQuery] string token, CancellationToken ct)
    {
        await _mediator.Send(new VerifyEmailCommand(userId, token), ct);
        return Ok(new { message = "Email verified" });
    }

    [Authorize]
    [HttpGet("me")]
    public async Task<ActionResult<UserDto>> GetMe(CancellationToken ct)
        => Ok(await _mediator.Send(new GetMeQuery(), ct));

    [Authorize]
    [HttpPost("change-password")]
    [EnableRateLimiting("AuthPolicy")]
    public async Task<IActionResult> ChangePassword(
        [FromBody] ChangePasswordCommand cmd, CancellationToken ct)
    {
        await _mediator.Send(cmd, ct);
        return NoContent();
    }
}
