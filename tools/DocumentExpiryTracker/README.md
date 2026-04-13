# Document Expiry Tracker

`DocumentExpiryTracker` is a production-oriented .NET 8 CLI tool for tracking personal document expiration dates using a local JSON file. It is designed to stay simple in V1 while keeping clean seams for future extensions such as OCR-based expiry extraction, email notifications, push notifications, or a different persistence layer.

## Features

- Local JSON storage with no database or cloud dependency
- Interface-based architecture for extensibility
- Manual expiry date entry via CLI
- Console notifications for scheduled runs
- Cross-platform .NET 8 console application

## Project Structure

```text
DocumentExpiryTracker/
├── DocumentExpiryTracker.csproj
├── Program.cs
├── documents.json
├── documents.example.json
├── Interfaces/
│   ├── IDocumentRepository.cs
│   ├── IExpiryProvider.cs
│   └── INotificationProvider.cs
├── Models/
│   └── Document.cs
├── Providers/
│   ├── ConsoleNotificationProvider.cs
│   └── ManualExpiryProvider.cs
├── Repositories/
│   └── JsonDocumentRepository.cs
└── Services/
    └── DocumentService.cs
```

## Build

```bash
dotnet build
```

## Run

Add a document:

```bash
dotnet run -- add
```

Check for documents that hit a notification threshold today:

```bash
dotnet run -- check
```

## Notification Behavior

New documents use these default thresholds:

- 30 days before expiry
- 7 days before expiry
- 1 day before expiry
- 0 days before expiry

These are stored with each document in `documents.json`, so they can be customized later without changing the code.

## Example `documents.json`

```json
[
  {
    "Name": "Passport",
    "FilePath": "/home/user/documents/passport.pdf",
    "ExpiryDate": "2030-06-15T00:00:00",
    "NotifyDaysBefore": [30, 7, 1, 0],
    "LastNotifiedDates": null
  }
]
```

## Scheduling

This CLI is intended to be scheduled daily.

- Windows: Task Scheduler
- Linux: cron or systemd timers

Run the `check` command once per day:

```bash
dotnet run -- check
```
