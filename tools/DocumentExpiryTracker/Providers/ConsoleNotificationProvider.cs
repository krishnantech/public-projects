using DocumentExpiryTracker.Interfaces;

namespace DocumentExpiryTracker.Providers;

public sealed class ConsoleNotificationProvider : INotificationProvider
{
    public Task NotifyAsync(string title, string message)
    {
        Console.WriteLine();
        Console.WriteLine($"[NOTIFICATION] {title}");
        Console.WriteLine(message);
        Console.WriteLine();

        return Task.CompletedTask;
    }
}
