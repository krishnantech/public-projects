using DocumentExpiryTracker.Interfaces;
using System.Globalization;

namespace DocumentExpiryTracker.Providers;

public sealed class ManualExpiryProvider : IExpiryProvider
{
    public Task<DateTime?> GetExpiryDateAsync(string filePath)
    {
        while (true)
        {
            Console.Write("Enter expiry date (yyyy-MM-dd): ");
            var input = Console.ReadLine();

            if (string.IsNullOrWhiteSpace(input))
            {
                Console.WriteLine("Expiry date is required.");
                continue;
            }

            if (DateTime.TryParseExact(
                    input.Trim(),
                    "yyyy-MM-dd",
                    CultureInfo.InvariantCulture,
                    DateTimeStyles.None,
                    out var parsedDate))
            {
                return Task.FromResult<DateTime?>(parsedDate.Date);
            }

            Console.WriteLine("Invalid date format. Please use yyyy-MM-dd.");
        }
    }
}
