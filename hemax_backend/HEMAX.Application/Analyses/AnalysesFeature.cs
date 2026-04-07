using HEMAX.Domain.Enums;
using MediatR;
using HEMAX.Application.Common.Models;

namespace HEMAX.Application.Analyses;


public record AnalysisDto(
    Guid Id,
    Guid UserId,
    AnalysisType Type,
    AnalysisSeverity Severity,
    string? TopFlag,
    string? SummaryUa,
    string? Language,
    DateTimeOffset CreatedAt,
    Guid? DoctorReviewedById,
    DateTimeOffset? DoctorReviewedAt,
    string? DoctorNote,
    string? FileUrl,
    string? FileName
);

public record AnalysisDetailDto(
    Guid Id,
    Guid UserId,
    AnalysisType Type,
    AnalysisSeverity Severity,
    string? TopFlag,
    string? SummaryUa,
    string? Language,
    string RawInputJson,
    string ResultJson,
    DateTimeOffset CreatedAt,
    Guid? DoctorReviewedById,
    DateTimeOffset? DoctorReviewedAt,
    string? DoctorNote,
    string? FileUrl,
    string? FileName
);

public record TimelinePoint(
    DateTimeOffset Date,
    double? Value,
    string? Flag,
    Guid AnalysisId
);

public record AnalysisComparisonDto(
    AnalysisDetailDto Older,
    AnalysisDetailDto Newer,
    Dictionary<string, ChangeIndicator> Changes
);

public record ChangeIndicator(
    double? OldValue,
    double? NewValue,
    string? OldFlag,
    string? NewFlag,
    string Direction
);

public record SubmitAnalysisCommand(
    AnalysisType Type,
    string PayloadJson,
    string? Language,
    bool MergeRecentLabs = false
) : IRequest<AnalysisDto>;

/// <summary>
/// Submit DERMA analysis with image upload + metadata.
///
/// Bug fix May 2026: <paramref name="Language"/> was previously dropped on
/// the floor — the frontend appended `language` to the FormData but no
/// place in the backend command shape accepted it, so the field went
/// silently into the void. DERMA's Python API doesn't currently have a
/// /derma/analyze/narrative variant (the response is class probabilities
/// + a class code, no human-readable explanation that would need
/// translation), so we don't forward Language to Python. We do store it
/// on the Analysis row so the UI's i18n layer can pick the right severity
/// label string at render time, and so the value participates in
/// "what language was this analysis filed in" filtering / display.
/// </summary>
public record SubmitDermaAnalysisCommand(
    Stream ImageStream,
    string ImageFileName,
    string ImageContentType,
    double? Age,
    string? Sex,
    string? Localization,
    int TopK,
    string? Language = null
) : IRequest<AnalysisDto>;

/// <summary>Doctor adds a note to a patient's analysis.</summary>
public record AnnotateAnalysisCommand(
    Guid AnalysisId,
    string Note
) : IRequest<AnalysisDto>;

public record DeleteAnalysisCommand(
    Guid AnalysisId
) : IRequest;

public record ExtractFromPdfCommand(
    Stream PdfStream,
    string FileName,
    string ContentType,
    string? Hint
) : IRequest<PdfExtractionDto>;

public record PdfExtractionDto(
    string DetectedKind,
    IReadOnlyDictionary<string, double> Values,
    IReadOnlyDictionary<string, string> Units,
    string? LabName,
    double Confidence,
    Guid PdfFileAssetId,
    string? PdfFileUrl
);

public record SubmitAnalysisFromPdfCommand(
    AnalysisType Type,
    string PayloadJson,
    string? Language,
    Guid PdfFileAssetId
) : IRequest<AnalysisDto>;

public record GetAnalysisHistoryQuery(
    Guid? UserId,            // null = current user
    AnalysisType? Type,
    AnalysisSeverity? MinSeverity,
    DateTimeOffset? From,
    DateTimeOffset? To,
    PageRequest Page
) : IRequest<PagedResult<AnalysisDto>>;

public record GetAnalysisByIdQuery(
    Guid Id,
    string? Language = null
) : IRequest<AnalysisDetailDto>;

public record GetHealthTimelineQuery(
    Guid? UserId,
    AnalysisType Type,
    string Field,
    DateTimeOffset? From,
    DateTimeOffset? To
) : IRequest<IReadOnlyList<TimelinePoint>>;

public record CompareAnalysesQuery(
    Guid OlderId,
    Guid NewerId
) : IRequest<AnalysisComparisonDto>;
