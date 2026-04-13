using DocumentExpiryTracker.Interfaces;
using DocumentExpiryTracker.Models;
using System.Text.Json;

namespace DocumentExpiryTracker.Repositories;

public sealed class JsonDocumentRepository : IDocumentRepository
{
    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        WriteIndented = true
    };

    private readonly string _filePath;

    public JsonDocumentRepository(string filePath)
    {
        _filePath = Path.GetFullPath(filePath);
    }

    public async Task<List<Document>> GetAllAsync()
    {
        if (!File.Exists(_filePath))
        {
            return [];
        }

        await using var stream = File.OpenRead(_filePath);
        var documents = await JsonSerializer.DeserializeAsync<List<Document>>(stream, SerializerOptions);

        return documents ?? [];
    }

    public async Task SaveAsync(List<Document> documents)
    {
        var directory = Path.GetDirectoryName(_filePath);
        if (!string.IsNullOrWhiteSpace(directory))
        {
            Directory.CreateDirectory(directory);
        }

        await using var stream = File.Create(_filePath);
        await JsonSerializer.SerializeAsync(stream, documents, SerializerOptions);
    }
}
