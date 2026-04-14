using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Domain.Entities;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;

namespace HEMAX.Infrastructure.Identity;

public class JwtTokenService : ITokenService
{
    private readonly IConfiguration _config;

    public JwtTokenService(IConfiguration config)
    {
        _config = config;
    }

    public string CreateAccessToken(ApplicationUser user, IEnumerable<string> roles)
    {
        var key       = _config["Jwt:Key"]      ?? throw new InvalidOperationException("Missing Jwt:Key");
        var issuer    = _config["Jwt:Issuer"]   ?? "hemax-backend";
        var audience  = _config["Jwt:Audience"] ?? "hemax-clients";
        var minutes   = int.Parse(_config["Jwt:AccessTokenExpirationMinutes"] ?? "15");

        var claims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub,    user.Id.ToString()),
            new(JwtRegisteredClaimNames.Email,  user.Email ?? ""),
            new(JwtRegisteredClaimNames.Jti,    Guid.NewGuid().ToString()),
            new(ClaimTypes.NameIdentifier,      user.Id.ToString()),
            new(ClaimTypes.Email,               user.Email ?? ""),
            new(ClaimTypes.Name,                user.UserName ?? user.Email ?? ""),
            new("first_name",                   user.FirstName),
            new("last_name",                    user.LastName),
        };
        foreach (var role in roles)
        {
            claims.Add(new Claim(ClaimTypes.Role, role));
        }

        var creds = new SigningCredentials(
            new SymmetricSecurityKey(Encoding.UTF8.GetBytes(key)),
            SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer:             issuer,
            audience:           audience,
            claims:             claims,
            notBefore:          DateTime.UtcNow,
            expires:            DateTime.UtcNow.AddMinutes(minutes),
            signingCredentials: creds);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    public string CreateRefreshToken()
    {
        var bytes = RandomNumberGenerator.GetBytes(64);
        return Convert.ToBase64String(bytes)
            .Replace("+", "-").Replace("/", "_").TrimEnd('=');
    }

    public string HashRefreshToken(string rawToken)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(rawToken));
        return Convert.ToHexString(bytes);
    }
}
