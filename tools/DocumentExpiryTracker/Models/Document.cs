namespace DocumentExpiryTracker.Models;

public sealed class Document
{
    public string Name { get; set; } = string.Empty;

    public string FilePath { get; set; } = string.Empty;

    public DateTime ExpiryDate { get; set; }

    public List<int> NotifyDaysBefore { get; set; } = [];

    public Dictionary<int, DateTime>? LastNotifiedDates { get; set; }
}
