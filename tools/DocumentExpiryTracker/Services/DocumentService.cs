using DocumentExpiryTracker.Interfaces;
using DocumentExpiryTracker.Models;

namespace DocumentExpiryTracker.Services;

public sealed class DocumentService
{
    private static readonly List<int> DefaultNotificationThresholds = [30, 7, 1, 0];

    private readonly IDocumentRepository _repository;
    private readonly IExpiryProvider _expiryProvider;
    private readonly INotificationProvider _notificationProvider;

    public DocumentService(
        IDocumentRepository repository,
        IExpiryProvider expiryProvider,
        INotificationProvider notificationProvider)
    {
        _repository = repository;
        _expiryProvider = expiryProvider;
        _notificationProvider = notificationProvider;
    }

    public async Task AddDocumentAsync()
    {
        Console.Write("Enter document name: ");
        var name = ReadRequiredValue("Document name is required.");

        Console.Write("Enter file path: ");
        var filePath = ReadRequiredValue("File path is required.");

        var expiryDate = await _expiryProvider.GetExpiryDateAsync(filePath);
        if (expiryDate is null)
        {
            Console.WriteLine("Unable to determine expiry date.");
            return;
        }

        var documents = await _repository.GetAllAsync();
        documents.Add(new Document
        {
            Name = name,
            FilePath = filePath,
            ExpiryDate = expiryDate.Value.Date,
            NotifyDaysBefore = [.. DefaultNotificationThresholds]
        });

        await _repository.SaveAsync(documents);

        Console.WriteLine("Document saved successfully.");
        Console.WriteLine($"Notification thresholds: {string.Join(", ", DefaultNotificationThresholds)} days before expiry.");
    }

    public async Task CheckExpirationsAsync()
    {
        var documents = await _repository.GetAllAsync();

        if (documents.Count == 0)
        {
            Console.WriteLine("No documents found.");
            return;
        }

        var today = DateTime.Today;
        var notificationsSent = 0;

        foreach (var document in documents)
        {
            document.NotifyDaysBefore ??= [];
            var daysRemaining = (document.ExpiryDate.Date - today).Days;

            if (!document.NotifyDaysBefore.Contains(daysRemaining))
            {
                continue;
            }

            var title = $"Document expiry reminder: {document.Name}";
            var message = BuildNotificationMessage(document, daysRemaining);
            await _notificationProvider.NotifyAsync(title, message);
            notificationsSent++;
        }

        if (notificationsSent == 0)
        {
            Console.WriteLine("No document notifications due today.");
        }
    }

    private static string BuildNotificationMessage(Document document, int daysRemaining)
    {
        return daysRemaining switch
        {
            < 0 => $"{document.Name} expired {-daysRemaining} day(s) ago on {document.ExpiryDate:yyyy-MM-dd}. File: {document.FilePath}",
            0 => $"{document.Name} expires today ({document.ExpiryDate:yyyy-MM-dd}). File: {document.FilePath}",
            _ => $"{document.Name} expires in {daysRemaining} day(s) on {document.ExpiryDate:yyyy-MM-dd}. File: {document.FilePath}"
        };
    }

    private static string ReadRequiredValue(string validationMessage)
    {
        while (true)
        {
            var input = Console.ReadLine();
            if (!string.IsNullOrWhiteSpace(input))
            {
                return input.Trim();
            }

            Console.WriteLine(validationMessage);
        }
    }
}
