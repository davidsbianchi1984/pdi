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

public record SealedInfo(
    [property: JsonPropertyName("cipher")] string Cipher,
    [property: JsonPropertyName("bound_to")] string BoundTo,
    [property: JsonPropertyName("created_at")] string CreatedAt,
    [property: JsonPropertyName("updated_at")] string UpdatedAt,
    [property: JsonPropertyName("ciphertext_bytes")] int CiphertextBytes);

public record ProvenanceAudit(
    [property: JsonPropertyName("count")] int Count);

public record ChainState(
    [property: JsonPropertyName("intact")] bool Intact);

public record RecordProvenance(
    [property: JsonPropertyName("key")] string Key,
    [property: JsonPropertyName("origin")] string Origin,
    [property: JsonPropertyName("sealed")] SealedInfo Sealed,
    [property: JsonPropertyName("audit")] ProvenanceAudit Audit,
    [property: JsonPropertyName("chain")] ChainState Chain);

public record LanguageInfo(
    [property: JsonPropertyName("code")] string Code,
    [property: JsonPropertyName("label")] string Label,
    [property: JsonPropertyName("notes_translated")] bool NotesTranslated);

public record LanguagesList(
    [property: JsonPropertyName("languages")] LanguageInfo[] Languages,
    [property: JsonPropertyName("default")] string Default);

public record LanguageChoice(
    [property: JsonPropertyName("language")] string Language,
    [property: JsonPropertyName("label")] string Label,
    [property: JsonPropertyName("mode")] string? Mode);

public record VerifyResult(
    [property: JsonPropertyName("intact")] bool Intact);

public record AuditEntry(
    [property: JsonPropertyName("seq")] int Seq,
    [property: JsonPropertyName("action")] string Action,
    [property: JsonPropertyName("ref")] string? Ref,
    [property: JsonPropertyName("at")] string At,
    [property: JsonPropertyName("category")] string? Category);

public record RobotSpec(
    [property: JsonPropertyName("model")] string Model,
    [property: JsonPropertyName("label")] string Label,
    [property: JsonPropertyName("maker")] string Maker);

public record RoboticsCatalog(
    [property: JsonPropertyName("robots")] RobotSpec[] Robots);

public record Robot(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("model")] string Model,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("status")] string? Status,
    [property: JsonPropertyName("collected")] int Collected);

public record IngestResult(
    [property: JsonPropertyName("sealed")] bool Sealed,
    [property: JsonPropertyName("key")] string Key);

public record RobotData(
    [property: JsonPropertyName("keys")] string[] Keys);

public record ComplianceProgram(
    [property: JsonPropertyName("key")] string Key,
    [property: JsonPropertyName("label")] string Label);

public record CompliancePrograms(
    [property: JsonPropertyName("programs")] ComplianceProgram[] Programs);

public record Transfer(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("recipient")] string Recipient,
    [property: JsonPropertyName("filename")] string Filename,
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("programs")] string[] Programs,
    [property: JsonPropertyName("expires_at")] string? ExpiresAt,
    [property: JsonPropertyName("receive_token")] string? ReceiveToken);

public record Intake(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("from_party")] string FromParty,
    [property: JsonPropertyName("purpose")] string? Purpose,
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("programs")] string[] Programs,
    [property: JsonPropertyName("filename")] string? Filename,
    [property: JsonPropertyName("submit_token")] string? SubmitToken);

public record IntakeFile(
    [property: JsonPropertyName("filename")] string? Filename,
    [property: JsonPropertyName("content")] string? Content);

public record SocialConn(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("platform")] string Platform,
    [property: JsonPropertyName("direction")] string Direction,
    [property: JsonPropertyName("handle")] string? Handle);

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

    public Task<RecordProvenance> Provenance(string token, string key) =>
        Send<RecordProvenance>(new HttpRequestMessage(
            HttpMethod.Get, $"/provenance/{key}"), token);

    public Task<LanguagesList> Languages(string token) =>
        Send<LanguagesList>(new HttpRequestMessage(HttpMethod.Get, "/languages"), token);

    public Task<LanguageChoice> Language(string token) =>
        Send<LanguageChoice>(new HttpRequestMessage(HttpMethod.Get, "/language"), token);

    public Task<LanguageChoice> SetLanguage(string token, string code,
                                            string mode = "pre") =>
        Send<LanguageChoice>(new HttpRequestMessage(HttpMethod.Put, "/language")
        {
            Content = JsonContent.Create(new { language = code, mode }),
        }, token);

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

    // -- robots as vault-backed data sources --

    public Task<RoboticsCatalog> Robotics(string token) =>
        Send<RoboticsCatalog>(new HttpRequestMessage(HttpMethod.Get, "/robotics/catalog"), token);

    public Task<Robot[]> Robots(string token) =>
        Send<Robot[]>(new HttpRequestMessage(HttpMethod.Get, "/robots"), token);

    public Task<Robot> BindRobot(string token, string model)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, "/robots")
        {
            Content = JsonContent.Create(new { model }),
        };
        return Send<Robot>(req, token);
    }

    public Task<IngestResult> Ingest(string token, string rid, string kind, string content)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, $"/robots/{rid}/ingest")
        {
            Content = JsonContent.Create(new { kind, content }),
        };
        return Send<IngestResult>(req, token);
    }

    public Task<RobotData> RobotKeys(string token, string rid) =>
        Send<RobotData>(new HttpRequestMessage(HttpMethod.Get, $"/robots/{rid}/data"), token);

    // -- compliance-grade secure transfers --

    public Task<CompliancePrograms> Programs(string token) =>
        Send<CompliancePrograms>(new HttpRequestMessage(
            HttpMethod.Get, "/compliance/programs"), token);

    public Task<Transfer[]> Transfers(string token) =>
        Send<Transfer[]>(new HttpRequestMessage(HttpMethod.Get, "/transfers"), token);

    public Task<Transfer> CreateTransfer(string token, string recipient,
                                         string filename, string content,
                                         string[] programs)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, "/transfers")
        {
            Content = JsonContent.Create(new { recipient, filename, content, programs }),
        };
        return Send<Transfer>(req, token);
    }

    public Task RevokeTransfer(string token, string tid) =>
        SendNoContent(new HttpRequestMessage(HttpMethod.Delete, $"/transfers/{tid}"), token);

    // -- secure intake --

    public Task<Intake[]> Intakes(string token) =>
        Send<Intake[]>(new HttpRequestMessage(HttpMethod.Get, "/intakes"), token);

    public Task<Intake> CreateIntake(string token, string fromParty,
                                     string? purpose, string[] programs)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, "/intakes")
        {
            Content = JsonContent.Create(new
            {
                from_party = fromParty,
                purpose = string.IsNullOrEmpty(purpose) ? null : purpose,
                programs,
            }),
        };
        return Send<Intake>(req, token);
    }

    public Task<IntakeFile> ReadIntakeFile(string token, string iid) =>
        Send<IntakeFile>(new HttpRequestMessage(
            HttpMethod.Get, $"/intakes/{iid}/file"), token);

    public Task CloseIntake(string token, string iid) =>
        SendNoContent(new HttpRequestMessage(HttpMethod.Delete, $"/intakes/{iid}"), token);

    // -- social-platform connectors --

    public Task<SocialConn[]> Connectors(string token) =>
        Send<SocialConn[]>(new HttpRequestMessage(HttpMethod.Get, "/connectors"), token);

    public Task<SocialConn> CreateConnector(string token, string platform,
                                            string direction, string? handle)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, "/connectors")
        {
            Content = JsonContent.Create(new
            {
                platform, direction,
                handle = string.IsNullOrEmpty(handle) ? null : handle,
            }),
        };
        return Send<SocialConn>(req, token);
    }

    public Task ConnectorIngest(string token, string cid, string content)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, $"/connectors/{cid}/ingest")
        {
            Content = JsonContent.Create(new { items = new[] { new { content } } }),
        };
        return SendNoContent(req, token);
    }

    public Task ConnectorPublish(string token, string cid, string content)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, $"/connectors/{cid}/publish")
        {
            Content = JsonContent.Create(new { content }),
        };
        return SendNoContent(req, token);
    }

    public Task RevokeConnector(string token, string cid) =>
        SendNoContent(new HttpRequestMessage(HttpMethod.Delete, $"/connectors/{cid}"), token);

    /// <summary>The sender's side: authenticated by the one-shot
    /// X-Submit-Token, not the tenant bearer.</summary>
    public async Task SubmitIntake(string iid, string submitToken,
                                   string filename, string content)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, $"/intakes/{iid}/submit")
        {
            Content = JsonContent.Create(new { filename, content }),
        };
        req.Headers.Add("X-Submit-Token", submitToken);
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
}
