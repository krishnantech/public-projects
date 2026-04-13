using DocumentExpiryTracker.Models;

namespace DocumentExpiryTracker.Interfaces;

public interface IDocumentRepository
{
    Task<List<Document>> GetAllAsync();

    Task SaveAsync(List<Document> documents);
}
