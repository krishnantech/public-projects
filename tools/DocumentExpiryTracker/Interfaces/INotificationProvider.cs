namespace DocumentExpiryTracker.Interfaces;

public interface INotificationProvider
{
    Task NotifyAsync(string title, string message);
}
