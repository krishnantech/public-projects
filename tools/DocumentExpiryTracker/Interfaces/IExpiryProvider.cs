namespace DocumentExpiryTracker.Interfaces;

public interface IExpiryProvider
{
    Task<DateTime?> GetExpiryDateAsync(string filePath);
}
