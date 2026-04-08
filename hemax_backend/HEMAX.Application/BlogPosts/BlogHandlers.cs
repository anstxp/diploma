using AutoMapper;
using HEMAX.Application.Common.Exceptions;
using HEMAX.Application.Common.Interfaces;
using HEMAX.Application.Common.Models;
using HEMAX.Domain.Entities;
using HEMAX.Domain.Enums;
using HEMAX.Domain.Exceptions;
using HEMAX.Infrastructure.Files;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace HEMAX.Application.BlogPosts;


public class CreateBlogPostHandler : IRequestHandler<CreateBlogPostCommand, Guid>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;

    public CreateBlogPostHandler(IHemaxDbContext db, ICurrentUserService current, IAuditService audit)
    {
        _db = db; _current = current; _audit = audit;
    }

    public async Task<Guid> Handle(CreateBlogPostCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var post = new BlogPost
        {
            AuthorId = _current.UserId.Value,
            Title    = cmd.Title.Trim(),
            Content  = cmd.Content,
        };
        if (cmd.Tags is not null) post.SetTagsList(cmd.Tags);

        _db.BlogPosts.Add(post);
        await _db.SaveChangesAsync(ct);

        await _audit.LogAsync(AuditAction.BlogPostCreated, "BlogPost", post.Id,
            new { title = post.Title }, ct);

        return post.Id;
    }
}


public class UpdateBlogPostHandler : IRequestHandler<UpdateBlogPostCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;

    public UpdateBlogPostHandler(IHemaxDbContext db, ICurrentUserService current, IAuditService audit)
    {
        _db = db; _current = current; _audit = audit;
    }

    public async Task Handle(UpdateBlogPostCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var post = await _db.BlogPosts.FirstOrDefaultAsync(p => p.Id == cmd.PostId, ct)
            ?? throw new EntityNotFoundException("BlogPost", cmd.PostId);

        // Author or admin
        if (post.AuthorId != _current.UserId && !_current.IsInRole(Roles.Administrator))
            throw new ForbiddenException("You can only edit your own posts");

        post.Title   = cmd.Title.Trim();
        post.Content = cmd.Content;
        if (cmd.Tags is not null) post.SetTagsList(cmd.Tags);

        await _db.SaveChangesAsync(ct);

        await _audit.LogAsync(AuditAction.BlogPostUpdated, "BlogPost", post.Id, null, ct);
    }
}


public class DeleteBlogPostHandler : IRequestHandler<DeleteBlogPostCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;

    public DeleteBlogPostHandler(IHemaxDbContext db, ICurrentUserService current, IAuditService audit)
    {
        _db = db; _current = current; _audit = audit;
    }

    public async Task Handle(DeleteBlogPostCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var post = await _db.BlogPosts
            .IgnoreQueryFilters()
            .FirstOrDefaultAsync(p => p.Id == cmd.PostId, ct)
            ?? throw new EntityNotFoundException("BlogPost", cmd.PostId);

        var isOwner = post.AuthorId == _current.UserId;
        var isAdmin = _current.IsInRole(Roles.Administrator);

        if (!isOwner && !isAdmin)
            throw new ForbiddenException("You can only delete your own posts (admins can delete any)");

        post.SoftDelete(_current.UserId);
        await _db.SaveChangesAsync(ct);

        await _audit.LogAsync(AuditAction.BlogPostDeleted, "BlogPost", post.Id,
            new { byAdmin = isAdmin && !isOwner }, ct);
    }
}


public class RecoverBlogPostHandler : IRequestHandler<RecoverBlogPostCommand>
{
    private readonly IHemaxDbContext _db;

    public RecoverBlogPostHandler(IHemaxDbContext db) => _db = db;

    public async Task Handle(RecoverBlogPostCommand cmd, CancellationToken ct)
    {
        var post = await _db.BlogPosts
            .IgnoreQueryFilters()
            .FirstOrDefaultAsync(p => p.Id == cmd.PostId, ct)
            ?? throw new EntityNotFoundException("BlogPost", cmd.PostId);

        post.IsDeleted   = false;
        post.DeletedAt   = null;
        post.DeletedById = null;
        await _db.SaveChangesAsync(ct);
    }
}


public class ToggleLikeHandler : IRequestHandler<ToggleLikeCommand, bool>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;

    public ToggleLikeHandler(IHemaxDbContext db, ICurrentUserService current)
    {
        _db = db; _current = current;
    }

    public async Task<bool> Handle(ToggleLikeCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var post = await _db.BlogPosts.FirstOrDefaultAsync(p => p.Id == cmd.PostId, ct)
            ?? throw new EntityNotFoundException("BlogPost", cmd.PostId);

        var existing = await _db.PostLikes
            .FirstOrDefaultAsync(l => l.PostId == cmd.PostId && l.UserId == _current.UserId, ct);

        if (existing is not null)
        {
            _db.PostLikes.Remove(existing);
            post.LikesCount = Math.Max(0, post.LikesCount - 1);
            await _db.SaveChangesAsync(ct);
            return false; // unliked
        }

        _db.PostLikes.Add(new PostLike
        {
            PostId = cmd.PostId,
            UserId = _current.UserId.Value,
        });
        post.LikesCount += 1;
        await _db.SaveChangesAsync(ct);
        return true; // liked
    }
}


public class CreateCommentHandler : IRequestHandler<CreateCommentCommand, CommentDto>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly INotificationService _notify;
    private readonly IMapper _mapper;

    public CreateCommentHandler(
        IHemaxDbContext db,
        ICurrentUserService current,
        INotificationService notify,
        IMapper mapper)
    {
        _db = db; _current = current; _notify = notify; _mapper = mapper;
    }

    public async Task<CommentDto> Handle(CreateCommentCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var post = await _db.BlogPosts.FirstOrDefaultAsync(p => p.Id == cmd.PostId, ct)
            ?? throw new EntityNotFoundException("BlogPost", cmd.PostId);

        var comment = new Comment
        {
            PostId   = cmd.PostId,
            AuthorId = _current.UserId.Value,
            Content  = cmd.Content,
        };
        _db.Comments.Add(comment);
        post.CommentsCount += 1;
        await _db.SaveChangesAsync(ct);

        // Notify post author (unless self-comment)
        if (post.AuthorId != _current.UserId)
        {
            await _notify.NotifyAsync(post.AuthorId, NotificationType.NewComment,
                "Новий коментар до вашого посту",
                cmd.Content.Length > 100 ? cmd.Content.Substring(0, 100) + "..." : cmd.Content,
                link: $"/blog/{post.Id}",
                relatedEntityId: post.Id, ct: ct);
        }

        var withAuthor = await _db.Comments
            .Include(c => c.Author)
            .FirstAsync(c => c.Id == comment.Id, ct);

        return _mapper.Map<CommentDto>(withAuthor);
    }
}

public class DeleteCommentHandler : IRequestHandler<DeleteCommentCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;

    public DeleteCommentHandler(IHemaxDbContext db, ICurrentUserService current, IAuditService audit)
    {
        _db = db; _current = current; _audit = audit;
    }

    public async Task Handle(DeleteCommentCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var comment = await _db.Comments.FirstOrDefaultAsync(c => c.Id == cmd.CommentId, ct)
            ?? throw new EntityNotFoundException("Comment", cmd.CommentId);

        var isOwner = comment.AuthorId == _current.UserId;
        var isAdmin = _current.IsInRole(Roles.Administrator);

        if (!isOwner && !isAdmin)
            throw new ForbiddenException();

        comment.SoftDelete(_current.UserId);

        var post = await _db.BlogPosts.IgnoreQueryFilters()
            .FirstOrDefaultAsync(p => p.Id == comment.PostId, ct);
        if (post is not null) post.CommentsCount = Math.Max(0, post.CommentsCount - 1);

        await _db.SaveChangesAsync(ct);

        await _audit.LogAsync(AuditAction.CommentDeleted, "Comment", comment.Id,
            new { byAdmin = isAdmin && !isOwner }, ct);
    }
}


public class GetBlogFeedHandler : IRequestHandler<GetBlogFeedQuery, PagedResult<BlogPostListItemDto>>
{
    private readonly IHemaxDbContext _db;
    private readonly IMapper _mapper;
    private readonly IFileUrlGenerator _urls;

    public GetBlogFeedHandler(IHemaxDbContext db, IMapper mapper, IFileUrlGenerator urls)
    {
        _db = db; _mapper = mapper; _urls = urls;
    }

    public async Task<PagedResult<BlogPostListItemDto>> Handle(
        GetBlogFeedQuery q, CancellationToken ct)
    {
        var query = _db.BlogPosts
            .Include(p => p.Author)
            .Where(p => p.IsPublished);

        if (q.AuthorId.HasValue)
            query = query.Where(p => p.AuthorId == q.AuthorId);

        if (!string.IsNullOrWhiteSpace(q.Tag))
        {
            var tag = q.Tag.Trim().ToLowerInvariant();
            query = query.Where(p => p.Tags.Contains(tag));
        }

        if (!string.IsNullOrWhiteSpace(q.Search))
        {
            var s = q.Search.Trim();
            query = query.Where(p => p.Title.Contains(s) || p.Content.Contains(s));
        }

        var total = await query.CountAsync(ct);
        var items = await query
            .OrderByDescending(p => p.CreatedAt)
            .Skip(q.Page.Skip).Take(q.Page.Take)
            .ToListAsync(ct);

        return new PagedResult<BlogPostListItemDto>
        {
            Items      = items.Select(p =>
            {
                var dto = _mapper.Map<BlogPostListItemDto>(p);
                if (!string.IsNullOrEmpty(p.CoverImageStorageKey))
                    return dto with { CoverImageUrl = _urls.GetDownloadUrl(p.CoverImageStorageKey) };
                return dto;
            }).ToList().AsReadOnly(),
            Page       = q.Page.Page,
            PageSize   = q.Page.PageSize,
            TotalItems = total,
        };
    }
}

public class GetBlogPostByIdHandler : IRequestHandler<GetBlogPostByIdQuery, BlogPostDto>
{
    private readonly IHemaxDbContext _db;
    private readonly IMapper _mapper;
    private readonly ICurrentUserService _current;
    private readonly IFileUrlGenerator _urls;

    public GetBlogPostByIdHandler(IHemaxDbContext db, IMapper mapper, ICurrentUserService current,
        IFileUrlGenerator urls)
    {
        _db = db; _mapper = mapper; _current = current; _urls = urls;
    }

    public async Task<BlogPostDto> Handle(GetBlogPostByIdQuery q, CancellationToken ct)
    {
        var post = await _db.BlogPosts
            .Include(p => p.Author)
            .FirstOrDefaultAsync(p => p.Id == q.PostId, ct)
            ?? throw new EntityNotFoundException("BlogPost", q.PostId);

        var dto = _mapper.Map<BlogPostDto>(post);

        // Fresh SAS URL for cover image, if any
        if (!string.IsNullOrEmpty(post.CoverImageStorageKey))
            dto = dto with { CoverImageUrl = _urls.GetDownloadUrl(post.CoverImageStorageKey) };

        var isLiked = false;
        if (_current.UserId is not null)
        {
            isLiked = await _db.PostLikes
                .AnyAsync(l => l.PostId == post.Id && l.UserId == _current.UserId, ct);
        }
        return dto with { IsLikedByMe = isLiked };
    }
}

public class GetCommentsHandler : IRequestHandler<GetCommentsQuery, PagedResult<CommentDto>>
{
    private readonly IHemaxDbContext _db;
    private readonly IMapper _mapper;

    public GetCommentsHandler(IHemaxDbContext db, IMapper mapper)
    {
        _db = db; _mapper = mapper;
    }

    public async Task<PagedResult<CommentDto>> Handle(GetCommentsQuery q, CancellationToken ct)
    {
        var query = _db.Comments
            .Include(c => c.Author)
            .Where(c => c.PostId == q.PostId);

        var total = await query.CountAsync(ct);
        var items = await query
            .OrderBy(c => c.CreatedAt)
            .Skip(q.Page.Skip).Take(q.Page.Take)
            .ToListAsync(ct);

        return new PagedResult<CommentDto>
        {
            Items      = items.Select(c => _mapper.Map<CommentDto>(c)).ToList().AsReadOnly(),
            Page       = q.Page.Page,
            PageSize   = q.Page.PageSize,
            TotalItems = total,
        };
    }
}

public class GetDeletedPostsHandler : IRequestHandler<GetDeletedPostsQuery, PagedResult<BlogPostListItemDto>>
{
    private readonly IHemaxDbContext _db;
    private readonly IMapper _mapper;

    public GetDeletedPostsHandler(IHemaxDbContext db, IMapper mapper)
    {
        _db = db; _mapper = mapper;
    }

    public async Task<PagedResult<BlogPostListItemDto>> Handle(
        GetDeletedPostsQuery q, CancellationToken ct)
    {
        var query = _db.BlogPosts
            .IgnoreQueryFilters()
            .Include(p => p.Author)
            .Where(p => p.IsDeleted);

        var total = await query.CountAsync(ct);
        var items = await query
            .OrderByDescending(p => p.DeletedAt)
            .Skip(q.Page.Skip).Take(q.Page.Take)
            .ToListAsync(ct);

        return new PagedResult<BlogPostListItemDto>
        {
            Items      = items.Select(p => _mapper.Map<BlogPostListItemDto>(p)).ToList().AsReadOnly(),
            Page       = q.Page.Page,
            PageSize   = q.Page.PageSize,
            TotalItems = total,
        };
    }
}


public class UploadBlogCoverHandler : IRequestHandler<UploadBlogCoverCommand, string>
{
    private const long MaxBlogCoverBytes = 10 * 1024 * 1024; // 10 MB

    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IFileStorageService _storage;
    private readonly IFileUrlGenerator _urls;
    private readonly IAuditService _audit;
    private readonly IFileSignatureValidator _signatures;

    public UploadBlogCoverHandler(
        IHemaxDbContext db, ICurrentUserService current,
        IFileStorageService storage, IFileUrlGenerator urls, IAuditService audit,
        IFileSignatureValidator signatures)
    {
        _db = db; _current = current;
        _storage = storage; _urls = urls; _audit = audit;
        _signatures = signatures;
    }

    public async Task<string> Handle(UploadBlogCoverCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var post = await _db.BlogPosts.FirstOrDefaultAsync(p => p.Id == cmd.PostId, ct)
            ?? throw new EntityNotFoundException("BlogPost", cmd.PostId);

        // Authorization: author or admin only
        if (post.AuthorId != _current.UserId.Value
            && !_current.IsInRole(Roles.Administrator))
        {
            throw new ForbiddenException();
        }

        await _signatures.ValidateAsync(
            cmd.FileStream, cmd.ContentType, FileKind.Image,
            maxBytes: MaxBlogCoverBytes, ct: ct);

        var (storageKey, _) = await _storage.SaveAsync(
            cmd.FileStream, cmd.FileName, cmd.ContentType, ct,
            category: "blog-covers");

        // Track in FileAsset
        _db.FileAssets.Add(new FileAsset
        {
            OwnerId         = _current.UserId.Value,
            Type            = FileAssetType.BlogAttachment,
            FileName        = cmd.FileName,
            ContentType     = cmd.ContentType,
            SizeBytes       = cmd.FileStream.CanSeek ? cmd.FileStream.Length : 0,
            StorageKey      = storageKey,
            PublicUrl       = null,  // generated on demand
            RelatedEntityId = post.Id,
        });

        // Update post
        post.CoverImageStorageKey = storageKey;
        post.CoverImageFileName   = cmd.FileName;
        post.UpdatedAt            = DateTimeOffset.UtcNow;

        await _db.SaveChangesAsync(ct);

        await _audit.LogAsync(AuditAction.BlogPostUpdated, "BlogPost", post.Id,
            new { action = "cover_uploaded", storageKey }, ct);

        return _urls.GetDownloadUrl(storageKey);
    }
}

public class RemoveBlogCoverHandler : IRequestHandler<RemoveBlogCoverCommand>
{
    private readonly IHemaxDbContext _db;
    private readonly ICurrentUserService _current;
    private readonly IAuditService _audit;

    public RemoveBlogCoverHandler(
        IHemaxDbContext db, ICurrentUserService current, IAuditService audit)
    {
        _db = db; _current = current; _audit = audit;
    }

    public async Task Handle(RemoveBlogCoverCommand cmd, CancellationToken ct)
    {
        if (_current.UserId is null) throw new UnauthorizedException();

        var post = await _db.BlogPosts.FirstOrDefaultAsync(p => p.Id == cmd.PostId, ct)
            ?? throw new EntityNotFoundException("BlogPost", cmd.PostId);

        if (post.AuthorId != _current.UserId.Value
            && !_current.IsInRole(Roles.Administrator))
        {
            throw new ForbiddenException();
        }

        // Note: we don't delete the blob itself (it may be referenced from
        // an audit log / related entity). We just unlink it from the post.
        post.CoverImageStorageKey = null;
        post.CoverImageFileName   = null;
        post.UpdatedAt            = DateTimeOffset.UtcNow;
        await _db.SaveChangesAsync(ct);

        await _audit.LogAsync(AuditAction.BlogPostUpdated, "BlogPost", post.Id,
            new { action = "cover_removed" }, ct);
    }
}
