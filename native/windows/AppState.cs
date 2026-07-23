using System;
using System.IO;
using System.Text.Json;

namespace PdiVault;

/// <summary>
/// The tenant bearer token + base URL, persisted to a small JSON file under
/// LocalApplicationData so the app resumes signed-in (unpackaged-safe).
/// </summary>
public sealed class AppState
{
    public static AppState Current { get; } = Load();

    public string? Token { get; set; }
    public string BaseUrl { get; set; } = "http://127.0.0.1:8000";

    public bool IsSignedIn => !string.IsNullOrEmpty(Token);

    private static string PathOnDisk =>
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                     "PdiVault", "session.json");

    public void SignIn(string token, string baseUrl)
    {
        Token = token; BaseUrl = baseUrl;
        Save();
    }

    public void SignOut()
    {
        Token = null;
        try { File.Delete(PathOnDisk); } catch { /* ignore */ }
    }

    private void Save()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(PathOnDisk)!);
        File.WriteAllText(PathOnDisk, JsonSerializer.Serialize(this));
    }

    private static AppState Load()
    {
        try
        {
            if (File.Exists(PathOnDisk))
                return JsonSerializer.Deserialize<AppState>(File.ReadAllText(PathOnDisk)) ?? new AppState();
        }
        catch { /* fall through to fresh state */ }
        return new AppState();
    }
}
