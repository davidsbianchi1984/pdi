using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace PdiVault;

// MARK: wire models (mirror pdi/api.py)

public record KeysResponse(
    [property: JsonPropertyName("keys")] string[] Keys);

public record VaultRecord(
    [property: JsonPropertyName("key")] string Key,
    [property: JsonPropertyName("value")] string Value,
    [property: JsonPropertyName("updated_at")] string? UpdatedAt);

public record VerifyResult(
    [property: JsonPropertyName("intact")] bool Intact);

public record AuditEntry(
    [property: JsonPropertyName("seq")] int Seq,
    [property: JsonPropertyName("action")] string Action,
    [property: JsonPropertyName("ref")] string? Ref,
    [property: JsonPropertyName("at")] string At,
    [property: JsonPropertyName("category")] string? Category);

/// <summary>
/// Async client for the PDI vault backend. Every call carries the tenant bearer
/// token (`pdi_...`), issued out of band and pasted at sign-in. Windows reaches
/// the local dev server directly on 127.0.0.1.
/// </summary>
public sealed class ApiClient
{
    public static ApiClient Shared { get; } = new();

    private readonly HttpClient _http = new() { BaseAddress = new Uri("http://127.0.0.1:8000") };

    public void SetBase(string url)
    {
        var t = url.TrimEnd('/');
        if (!string.IsNullOrWhiteSpace(t)) _http.BaseAddress = new Uri(t);
    }

    private async Task<T> Send<T>(HttpRequestMessage req, string token)
    {
        req.Headers.Add("authorization", $"Bearer {token}");
        var res = await _http.SendAsync(req);
        var body = await res.Content.ReadAsStringAsync();
        if (!res.IsSuccessStatusCode)
        {
            string? detail = null;
            try { detail = JsonDocument.Parse(body).RootElement.GetProperty("detail").GetString(); }
            catch { /* non-JSON error body */ }
            throw new HttpRequestException(detail ?? $"HTTP {(int)res.StatusCode}");
        }
        return JsonSerializer.Deserialize<T>(string.IsNullOrEmpty(body) ? "{}" : body)!;
    }

    private async Task SendNoContent(HttpRequestMessage req, string token)
    {
        req.Headers.Add("authorization", $"Bearer {token}");
        var res = await _http.SendAsync(req);
        if (!res.IsSuccessStatusCode)
        {
            var body = await res.Content.ReadAsStringAsync();
            string? detail = null;
            try { detail = JsonDocument.Parse(body).RootElement.GetProperty("detail").GetString(); }
            catch { /* ignore */ }
            throw new HttpRequestException(detail ?? $"HTTP {(int)res.StatusCode}");
        }
    }

    /// <summary>List record keys — also the sign-in validation call.</summary>
    public async Task<string[]> Keys(string token) =>
        (await Send<KeysResponse>(new HttpRequestMessage(HttpMethod.Get, "/records"), token)).Keys;

    public Task<VaultRecord> Record(string token, string key) =>
        Send<VaultRecord>(new HttpRequestMessage(HttpMethod.Get, $"/records/{key}"), token);

    public Task PutRecord(string token, string key, string value)
    {
        var req = new HttpRequestMessage(HttpMethod.Put, "/records")
        {
            Content = JsonContent.Create(new { key, value }),
        };
        return SendNoContent(req, token);
    }

    public Task DeleteRecord(string token, string key) =>
        SendNoContent(new HttpRequestMessage(HttpMethod.Delete, $"/records/{key}"), token);

    public Task<VerifyResult> AuditVerify(string token) =>
        Send<VerifyResult>(new HttpRequestMessage(HttpMethod.Get, "/audit/verify"), token);

    public Task<AuditEntry[]> AuditEntries(string token) =>
        Send<AuditEntry[]>(new HttpRequestMessage(HttpMethod.Get, "/audit"), token);
}
