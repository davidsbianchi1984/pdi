# PDI Vault — Windows (WinUI 3)

A native Windows desktop app in C# / WinUI 3 (Windows App SDK), wired to the PDI
vault backend. Same token sign-in and three screens as the other targets —
**Overview → Vault → Audit** — behind a `NavigationView`.

## Run

Requires the **.NET 8 SDK** and the **Windows App SDK** workload (Visual Studio
2022 → *".NET Desktop"* + *"Windows App SDK"*, or `winget install
Microsoft.WindowsAppRuntime.1.6`).

**Visual Studio:** open `PdiVault.csproj`, pick the `x64` configuration, press
**F5**.

**Command line:**

```powershell
cd native\windows
dotnet build -c Debug -r win-x64
dotnet run -c Debug -r win-x64
```

Start the backend first (Windows reaches `localhost` directly):

```powershell
# from the repo root
$env:PDI_CORS_ORIGINS = "*"; uvicorn pdi.api:app
```

Sign in by pasting a tenant token (`pdi_…`). The default base URL is
`http://127.0.0.1:8000` (see `ApiClient.cs`). The app is built **unpackaged**
(`WindowsPackageType=None`), so it is not subject to the MSIX loopback
restriction and can call `127.0.0.1` without an exemption.

## Layout

| File | Role |
| --- | --- |
| `PdiVault.csproj` | net8.0-windows target, WindowsAppSDK, unpackaged |
| `App.xaml` / `.cs` | app entry + the palette resource dictionary |
| `MainWindow.xaml` / `.cs` | root frame; routes to Welcome or Shell by state |
| `Views/ShellPage.xaml` | `NavigationView` host + sign-out |
| `Views/WelcomePage` | token sign-in → validated via `/records` |
| `Views/OverviewPage` | record count + audit status |
| `Views/VaultPage` | seal / reveal / delete records (`/records`) |
| `Views/AuditPage` | integrity badge + entries (`/audit`) |
| `Views/RobotsPage` | bind + sealed ingest (`/robots`, `/robots/{rid}/ingest`) |
| `Views/TransfersPage` | compliance transfers (`/transfers`, `/compliance/programs`) |
| `ApiClient.cs` | `HttpClient` client + records |
| `AppState.cs` | token + base URL, persisted to LocalAppData |
