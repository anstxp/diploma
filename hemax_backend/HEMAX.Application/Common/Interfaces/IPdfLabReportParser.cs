namespace HEMAX.Application.Common.Interfaces;

public record LabReportExtraction(
    string DetectedKind,
    IReadOnlyDictionary<string, double> Values,
    IReadOnlyDictionary<string, string> Units,
    string? LabName,
    double Confidence,
    string RawText
);

public interface IPdfLabReportParser
{
    Task<LabReportExtraction> ParseAsync(
        Stream pdfStream,
        string? hint,
        CancellationToken ct);
}
