using FluentValidation;

namespace HEMAX.Application.Analyses;

public class SubmitAnalysisCommandValidator : AbstractValidator<SubmitAnalysisCommand>
{
    public SubmitAnalysisCommandValidator()
    {
        RuleFor(x => x.Type).IsInEnum();
        RuleFor(x => x.PayloadJson).NotEmpty();
        RuleFor(x => x.Language).Must(l => l == null || l == "uk" || l == "en")
            .WithMessage("Language must be 'uk', 'en', or null");
    }
}

public class SubmitDermaAnalysisCommandValidator : AbstractValidator<SubmitDermaAnalysisCommand>
{
    public SubmitDermaAnalysisCommandValidator()
    {
        RuleFor(x => x.ImageStream).NotNull();
        RuleFor(x => x.ImageFileName).NotEmpty().MaximumLength(256);
        RuleFor(x => x.ImageContentType)
            .Must(ct => ct == "image/jpeg" || ct == "image/png" || ct == "image/jpg")
            .WithMessage("Content type must be image/jpeg or image/png");
        RuleFor(x => x.Age).InclusiveBetween(0, 120).When(x => x.Age.HasValue);
        RuleFor(x => x.TopK).InclusiveBetween(1, 7);
    }
}

public class AnnotateAnalysisCommandValidator : AbstractValidator<AnnotateAnalysisCommand>
{
    public AnnotateAnalysisCommandValidator()
    {
        RuleFor(x => x.AnalysisId).NotEmpty();
        RuleFor(x => x.Note).NotEmpty().MaximumLength(4000);
    }
}

public class GetAnalysisHistoryQueryValidator : AbstractValidator<GetAnalysisHistoryQuery>
{
    public GetAnalysisHistoryQueryValidator()
    {
        RuleFor(x => x.Page.Page).GreaterThan(0);
        RuleFor(x => x.Page.PageSize).InclusiveBetween(1, 100);
    }
}

public class GetHealthTimelineQueryValidator : AbstractValidator<GetHealthTimelineQuery>
{
    public GetHealthTimelineQueryValidator()
    {
        RuleFor(x => x.Type).IsInEnum();
        RuleFor(x => x.Field).NotEmpty().MaximumLength(50);
    }
}
