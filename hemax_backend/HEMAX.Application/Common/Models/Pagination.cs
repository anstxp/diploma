namespace HEMAX.Application.Common.Models;

/// <summary>Pagination request.</summary>
public record PageRequest
{
    public int Page     { get; init; } = 1;
    public int PageSize { get; init; } = 20;

    public int Skip => (Math.Max(1, Page) - 1) * PageSize;
    public int Take => Math.Clamp(PageSize, 1, 100);
}

public record PagedResult<T>
{
    public IReadOnlyList<T> Items { get; init; } = Array.Empty<T>();
    public int Page       { get; init; }
    public int PageSize   { get; init; }
    public int TotalItems { get; init; }
    public int TotalPages => PageSize == 0 ? 0 : (int)Math.Ceiling((double)TotalItems / PageSize);
    public bool HasPrevious => Page > 1;
    public bool HasNext     => Page < TotalPages;
}

public record Result<T>
{
    public bool IsSuccess { get; init; }
    public T?   Value     { get; init; }
    public string? Error  { get; init; }
    public string? ErrorCode { get; init; }

    public static Result<T> Success(T value) => new() { IsSuccess = true, Value = value };
    public static Result<T> Failure(string error, string? code = null) =>
        new() { IsSuccess = false, Error = error, ErrorCode = code };
}
