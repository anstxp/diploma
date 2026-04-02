using HEMAX.Domain.Common;

namespace HEMAX.Domain.Entities;

public class BlogPost : SoftDeletableEntity
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid AuthorId { get; set; }
    public ApplicationUser? Author { get; set; }

    public string Title { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;

    public string Tags { get; set; } = string.Empty;

    public string? CoverImageStorageKey { get; set; }

    public string? CoverImageFileName { get; set; }

    public bool IsPublished { get; set; } = true;

    public int LikesCount    { get; set; }
    public int CommentsCount { get; set; }

    // ─── Navigation ───
    public ICollection<Comment>  Comments  { get; set; } = new List<Comment>();
    public ICollection<PostLike> Likes     { get; set; } = new List<PostLike>();

    // ─── Helpers ───
    public IEnumerable<string> GetTagsList() =>
        Tags.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

    public void SetTagsList(IEnumerable<string> tags) =>
        Tags = string.Join(",", tags.Select(t => t.Trim().ToLowerInvariant()).Distinct());
}

public class Comment : SoftDeletableEntity
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid PostId { get; set; }
    public BlogPost? Post { get; set; }

    public Guid AuthorId { get; set; }
    public ApplicationUser? Author { get; set; }

    public string Content { get; set; } = string.Empty;
}

public class PostLike
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid PostId { get; set; }
    public BlogPost? Post { get; set; }

    public Guid UserId { get; set; }
    public ApplicationUser? User { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
}
