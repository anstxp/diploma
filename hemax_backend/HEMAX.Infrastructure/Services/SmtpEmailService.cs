using System.Net;
using System.Net.Mail;
using HEMAX.Application.Common.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace HEMAX.Infrastructure.Services;

public class SmtpEmailService : IEmailService
{
    private readonly IConfiguration _config;
    private readonly ILogger<SmtpEmailService> _logger;

    public SmtpEmailService(IConfiguration config, ILogger<SmtpEmailService> logger)
    {
        _config = config;
        _logger = logger;
    }

    public Task SendEmailVerificationAsync(string toEmail, string verificationLink, CancellationToken ct)
        => SendAsync(toEmail, "Verify your HEMAX email",
            $"<p>Welcome to HEMAX!</p>" +
            $"<p>Please verify your email by clicking " +
            $"<a href=\"{verificationLink}\">this link</a> or copying it to a browser:</p>" +
            $"<p><code>{verificationLink}</code></p>" +
            $"<p>The link expires in 24 hours.</p>", ct);

    public Task SendDoctorInviteAsync(string toEmail, string doctorName, string acceptLink, CancellationToken ct)
        => SendAsync(toEmail, "You have been invited as a patient",
            $"<p>Dr. {doctorName} has invited you to be their patient on HEMAX.</p>" +
            $"<p>To accept or decline, please log in to HEMAX or click " +
            $"<a href=\"{acceptLink}\">this link</a>.</p>", ct);

    public Task SendPasswordResetAsync(string toEmail, string resetLink, CancellationToken ct)
        => SendAsync(toEmail, "HEMAX Password reset",
            $"<p>Click <a href=\"{resetLink}\">this link</a> to reset your password.</p>" +
            $"<p>If you did not request this, ignore the email.</p>", ct);

    private async Task SendAsync(string toEmail, string subject, string htmlBody, CancellationToken ct)
    {
        var enabled  = _config.GetValue("Smtp:Enabled", false);
        var fromAddr = _config["Smtp:From"] ?? "noreply@hemax.local";
        var fromName = _config["Smtp:FromName"] ?? "HEMAX";

        if (!enabled)
        {
            _logger.LogInformation(
                "📧 [DEV] Would send email\n  To: {To}\n  Subject: {Subject}\n  Body: {Body}",
                toEmail, subject, htmlBody);
            return;
        }

        var host = _config["Smtp:Host"] ?? "localhost";
        var port = _config.GetValue("Smtp:Port", 587);
        var user = _config["Smtp:User"];
        var pass = _config["Smtp:Password"];

        using var client = new SmtpClient(host, port);
        client.EnableSsl = _config.GetValue("Smtp:UseSsl", true);
        if (!string.IsNullOrEmpty(user))
            client.Credentials = new NetworkCredential(user, pass);

        using var msg = new MailMessage
        {
            From       = new MailAddress(fromAddr, fromName),
            Subject    = subject,
            Body       = htmlBody,
            IsBodyHtml = true,
        };
        msg.To.Add(toEmail);

        try
        {
            await client.SendMailAsync(msg, ct);
            _logger.LogInformation("Email sent to {To}: {Subject}", toEmail, subject);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to send email to {To}", toEmail);
            throw;
        }
    }
}
