using DocumentExpiryTracker.Interfaces;
using DocumentExpiryTracker.Providers;
using DocumentExpiryTracker.Repositories;
using DocumentExpiryTracker.Services;

namespace DocumentExpiryTracker;

internal static class Program
{
    public static async Task<int> Main(string[] args)
    {
        IDocumentRepository repository = new JsonDocumentRepository("documents.json");
        IExpiryProvider expiryProvider = new ManualExpiryProvider();
        INotificationProvider notificationProvider = new ConsoleNotificationProvider();

        var documentService = new DocumentService(
            repository,
            expiryProvider,
            notificationProvider);

        if (args.Length == 0)
        {
            ShowUsage();
            return 1;
        }

        var command = args[0].Trim().ToLowerInvariant();

        switch (command)
        {
            case "add":
                await documentService.AddDocumentAsync();
                return 0;

            case "check":
                await documentService.CheckExpirationsAsync();
                return 0;

            case "help":
            case "--help":
            case "-h":
                ShowUsage();
                return 0;

            default:
                Console.WriteLine($"Unknown command: {args[0]}");
                ShowUsage();
                return 1;
        }
    }

    private static void ShowUsage()
    {
        Console.WriteLine("Document Expiry Tracker");
        Console.WriteLine();
        Console.WriteLine("Usage:");
        Console.WriteLine("  dotnet run -- add");
        Console.WriteLine("  dotnet run -- check");
    }
}
