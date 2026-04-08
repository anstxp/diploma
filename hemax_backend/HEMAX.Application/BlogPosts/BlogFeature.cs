using HEMAX.Application.Common.Models;
using MediatR;

namespace HEMAX.Application.BlogPosts;


public record BlogPostDto(
    Guid Id,
    Guid AuthorId,
    string AuthorName,
    string? AuthorAvatarUrl,
    string Title,
    string Content,
    IReadOnlyList<string> Tags,
    string? CoverImageUrl,
    int LikesCount,
    int CommentsCount,
    bool IsPublished,
    bool IsDeleted,
    bool IsLikedByMe,
    DateTimeOffset CreatedAt,
    DateTimeOffset? UpdatedAt
);

public record BlogPostListItemDto(
    Guid Id,
    Guid AuthorId,
    string AuthorName,
    string? AuthorAvatarUrl,
    string Title,
    string ContentPreview, // First ~200 chars
    IReadOnlyList<string> Tags,
    string? CoverImageUrl,
    int LikesCount,
    int CommentsCount,
    DateTimeOffset CreatedAt
);

public record CommentDto(
    Guid Id,
    Guid PostId,
    Guid AuthorId,
    string AuthorName,
    string? AuthorAvatarUrl,
    string Content,
    bool IsDeleted,
    DateTimeOffset CreatedAt
);


public record CreateBlogPostCommand(
    string Title,
    string Content,
    IReadOnlyList<string>? Tags
) : IRequest<Guid>;

public record UpdateBlogPostCommand(
    Guid PostId,
    string Title,
    string Content,
    IReadOnlyList<string>? Tags
) : IRequest;

public record DeleteBlogPostCommand(
    Guid PostId
) : IRequest;

public record UploadBlogCoverCommand(
    Guid PostId,
    Stream FileStream,
    string FileName,
    string ContentType
) : IRequest<string>;

public record RemoveBlogCoverCommand(
    Guid PostId
) : IRequest;

public record RecoverBlogPostCommand(
    Guid PostId
) : IRequest;

public record ToggleLikeCommand(
    Guid PostId
) : IRequest<bool>; // returns new like state


public record CreateCommentCommand(
    Guid PostId,
    string Content
) : IRequest<CommentDto>;

public record DeleteCommentCommand(
    Guid CommentId
) : IRequest;

public record GetBlogFeedQuery(
    string? Tag,        // filter by single tag
    string? Search,     // full-text search on title/content
    Guid? AuthorId,     // author's posts
    PageRequest Page
) : IRequest<PagedResult<BlogPostListItemDto>>;

public record GetBlogPostByIdQuery(
    Guid PostId
) : IRequest<BlogPostDto>;

public record GetCommentsQuery(
    Guid PostId,
    PageRequest Page
) : IRequest<PagedResult<CommentDto>>;

public record GetDeletedPostsQuery(
    PageRequest Page
) : IRequest<PagedResult<BlogPostListItemDto>>;
