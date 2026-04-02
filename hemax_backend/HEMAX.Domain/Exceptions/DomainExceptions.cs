namespace HEMAX.Domain.Exceptions;

public abstract class DomainException : Exception
{
    protected DomainException(string message) : base(message) { }
}

public class EntityNotFoundException : DomainException
{
    public string EntityName { get; }
    public object Key { get; }

    public EntityNotFoundException(string entityName, object key)
        : base($"{entityName} with key '{key}' was not found.")
    {
        EntityName = entityName;
        Key = key;
    }
}

public class ForbiddenAccessException : DomainException
{
    public ForbiddenAccessException(string message = "You do not have permission to perform this action.")
        : base(message) { }
}

public class BusinessRuleViolationException : DomainException
{
    public string Code { get; }

    public BusinessRuleViolationException(string code, string message)
        : base(message)
    {
        Code = code;
    }
}

public class DuplicateEntityException : DomainException
{
    public DuplicateEntityException(string message) : base(message) { }
}
