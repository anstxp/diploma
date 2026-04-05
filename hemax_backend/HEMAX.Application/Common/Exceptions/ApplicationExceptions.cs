namespace HEMAX.Application.Common.Exceptions;

public class ValidationException : Exception
{
    public IDictionary<string, string[]> Errors { get; }

    public ValidationException()
        : base("One or more validation failures have occurred.")
    {
        Errors = new Dictionary<string, string[]>();
    }

    public ValidationException(IEnumerable<FluentValidation.Results.ValidationFailure> failures)
        : this()
    {
        Errors = failures
            .GroupBy(e => e.PropertyName, e => e.ErrorMessage)
            .ToDictionary(g => g.Key, g => g.ToArray());
    }
}

public class UnauthorizedException : Exception
{
    public UnauthorizedException(string message = "Authentication required")
        : base(message) { }
}

public class ForbiddenException : Exception
{
    public ForbiddenException(string message = "You are not allowed to perform this action")
        : base(message) { }
}
