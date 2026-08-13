using System;
using System.Collections.Generic;
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

public record ReceivedFileOut(
    [property: JsonPropertyName("filename")] string? Filename,
    [property: JsonPropertyName("content")] string? Content);

public record BlueprintOut(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("industry")] string Industry);

public record PositionsListOut(
    [property: JsonPropertyName("count")] int Count,
    [property: JsonPropertyName("ids")] string[] Ids);

public record BaaStandingOut(
    [property: JsonPropertyName("executed")] bool Executed,
    [property: JsonPropertyName("effective_date")] string? EffectiveDate,
    [property: JsonPropertyName("note")] string? Note);

public record HealthOut(
    [property: JsonPropertyName("status")] string Status);

public record HostingModeOut(
    [property: JsonPropertyName("title")] string Title,
    [property: JsonPropertyName("price")] string Price,
    [property: JsonPropertyName("means")] string Means,
    [property: JsonPropertyName("free_because")] string? FreeBecause,
    [property: JsonPropertyName("we_are_responsible_for")] string[] We,
    [property: JsonPropertyName("you_are_responsible_for")] string[] You,
    [property: JsonPropertyName("mode")] string? Mode);

public record HostingModesOut(
    [property: JsonPropertyName("modes")] System.Collections.Generic.Dictionary<string, HostingModeOut> Modes);

public record HistoryRowOut([property: JsonPropertyName("mode")] string? Mode);

public record HostingHistoryOut(
    [property: JsonPropertyName("history")] HistoryRowOut[] History);

public record OperationsEntryOut([property: JsonPropertyName("key")] string Key);

public record OperationsOut(
    [property: JsonPropertyName("entries")] OperationsEntryOut[] Entries,
    [property: JsonPropertyName("note")] string Note);

public record AuditActionOut(
    [property: JsonPropertyName("action")] string Action,
    [property: JsonPropertyName("category")] string Category);

public record AuditSchemaOut(
    [property: JsonPropertyName("actions")] AuditActionOut[] Actions,
    [property: JsonPropertyName("retention")] string Retention);

public record BequestRow(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("grantee_name")] string GranteeName,
    [property: JsonPropertyName("condition")] string? Condition,
    [property: JsonPropertyName("key_prefixes")] string[] KeyPrefixes,
    [property: JsonPropertyName("activated")] bool Activated,
    [property: JsonPropertyName("revoked")] bool Revoked,
    [property: JsonPropertyName("grant_token")] string? GrantToken);

public record RevokedOut([property: JsonPropertyName("revoked")] bool Revoked);

public record KeysListOut([property: JsonPropertyName("keys")] string[] Keys);

public record ContribCount(
    [property: JsonPropertyName("count")] int Count,
    [property: JsonPropertyName("keys")] string[] Keys);

public record ContribOut(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("key")] string Key,
    [property: JsonPropertyName("sealed")] bool Sealed);

public record RetentionPolicyOut(
    [property: JsonPropertyName("recovery_window")] string RecoveryWindow,
    [property: JsonPropertyName("windows")] string[] Windows);

public record SweepOut(
    [property: JsonPropertyName("purged_tenants")] int PurgedTenants,
    [property: JsonPropertyName("expired_records")] int ExpiredRecords,
    [property: JsonPropertyName("recovery_window")] string RecoveryWindow);

public record TenantMade(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("token")] string Token);

public record OkOut([property: JsonPropertyName("id")] string? Id);

public record MintedTokenOut([property: JsonPropertyName("token")] string Token);

public record RetentionOut([property: JsonPropertyName("retention")] string Retention);

public record BaaOut(
    [property: JsonPropertyName("executed")] bool Executed,
    [property: JsonPropertyName("customer_legal_name")] string? CustomerLegalName,
    [property: JsonPropertyName("operator_legal_name")] string? OperatorLegalName,
    [property: JsonPropertyName("effective_date")] string? EffectiveDate);

public record GateCeilingOut(
    [property: JsonPropertyName("rule")] string Rule,
    [property: JsonPropertyName("may")] System.Collections.Generic.Dictionary<string, string> May,
    [property: JsonPropertyName("may_never")] System.Collections.Generic.Dictionary<string, string> MayNever);

public record GateChannelOut(
    [property: JsonPropertyName("configured")] bool Configured,
    [property: JsonPropertyName("signed")] bool? Signed);

public record RosterEntryOut(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("role")] string Role);

public record GateRosterOut(
    [property: JsonPropertyName("configured")] bool Configured,
    [property: JsonPropertyName("roster")] RosterEntryOut[] Roster,
    [property: JsonPropertyName("anybody_on_shift")] bool AnybodyOnShift);

public record RemovedOut([property: JsonPropertyName("removed")] bool Removed);

public record TzOut(
    [property: JsonPropertyName("tenant_id")] string TenantId,
    [property: JsonPropertyName("timezone")] string Timezone);

public record GatePageOut(
    [property: JsonPropertyName("id")] string? Id,
    [property: JsonPropertyName("state")] string? State);

public record CarrierBeacon(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("ref_kind")] string RefKind,
    [property: JsonPropertyName("label")] string Label,
    [property: JsonPropertyName("disclose")] string Disclose,
    [property: JsonPropertyName("state")] string State,
    [property: JsonPropertyName("scans")] int Scans,
    [property: JsonPropertyName("active")] bool Active);

public record LiftedOut(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("active")] bool Active);

// What a scanner sees. `contents` is always null on the wire and that is
// the feature: the code proves custody, it does not open the thing.
public record ScanCardOut(
    [property: JsonPropertyName("reference")] string Reference,
    [property: JsonPropertyName("kind")] string Kind,
    [property: JsonPropertyName("state")] string State,
    [property: JsonPropertyName("under_custody")] bool UnderCustody,
    [property: JsonPropertyName("badge")] string Badge,
    [property: JsonPropertyName("note")] string Note);

public record CustodyEntryOut(
    [property: JsonPropertyName("event")] string Event,
    [property: JsonPropertyName("actor")] string Actor,
    [property: JsonPropertyName("at")] string At);

public record CustodyChainOut(
    [property: JsonPropertyName("chain_of_custody")] CustodyEntryOut[] ChainOfCustody,
    [property: JsonPropertyName("audit_chain_intact")] bool AuditChainIntact);

public record FoundAckOut(
    [property: JsonPropertyName("beacon")] string Beacon,
    [property: JsonPropertyName("recorded")] bool Recorded,
    [property: JsonPropertyName("note")] string Note);

public record RingRowOut(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("kind")] string? Kind,
    [property: JsonPropertyName("note")] string? Note,
    [property: JsonPropertyName("state")] string? State,
    [property: JsonPropertyName("outcome")] string? Outcome,
    [property: JsonPropertyName("created_at")] string? CreatedAt);

public record PairInfoOut(
    [property: JsonPropertyName("console_url")] string ConsoleUrl,
    [property: JsonPropertyName("how")] string[] How,
    [property: JsonPropertyName("note")] string Note);

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

public record KeyVersion(
    [property: JsonPropertyName("version")] int Version,
    [property: JsonPropertyName("active")] bool Active,
    [property: JsonPropertyName("created_at")] string? CreatedAt);

public record KeysInfo(
    [property: JsonPropertyName("provider")] string Provider,
    [property: JsonPropertyName("versions")] KeyVersion[] Versions);

public record RetireResult(
    [property: JsonPropertyName("retired")] int Retired,
    [property: JsonPropertyName("versions")] KeyVersion[] Versions);

public record ImproveItem(
    [property: JsonPropertyName("category")] string Category,
    [property: JsonPropertyName("message")] string Message,
    [property: JsonPropertyName("status")] string Status);

public record ImproveState(
    [property: JsonPropertyName("mine")] ImproveItem[] Mine,
    [property: JsonPropertyName("tally")] System.Collections.Generic.Dictionary<string, int> Tally,
    [property: JsonPropertyName("total")] int Total);

public record AccessReceipt(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("note")] string? Note);

public record AccessReportRow(
    [property: JsonPropertyName("doing")] string Doing,
    [property: JsonPropertyName("wall")] string Wall,
    [property: JsonPropertyName("help")] string? Help,
    [property: JsonPropertyName("lang")] string Lang,
    [property: JsonPropertyName("created_at")] string CreatedAt);

public record AccessReportsState(
    [property: JsonPropertyName("reports")] AccessReportRow[] Reports,
    [property: JsonPropertyName("total")] int Total);

/// <summary>
/// Async client for the PDI vault backend. Every call carries the tenant bearer
/// token (`pdi_...`), issued out of band and pasted at sign-in. Windows reaches
/// the local dev server directly on 127.0.0.1.
/// </summary>
/// The export bundle, counted rather than modelled: reading every column of
/// every table into C# types would be a second copy of the schema.
public sealed class TenantExport
{
    public Dictionary<string, List<Dictionary<string, object>>> Tables { get; set; } = new();
    public string Note { get; set; } = "";
}

public sealed class ApiClient
{
    public static ApiClient Shared { get; } = new();

    private readonly HttpClient _http = new() { BaseAddress = new Uri("http://127.0.0.1:8000") };

    /// <summary>Every request this client sends, and the one place the
    /// reader's language is attached to it.
    ///
    /// <para>The header used to be set in the shared send helper — and the
    /// calls that went straight to <c>_http.SendAsync</c> instead never got
    /// it. Those are the uploads, the streams and the raw-response reads, and
    /// every refusal they draw arrived in English no matter what the machine
    /// was set to. A funnel only funnels what goes into it.</para></summary>
    private Task<HttpResponseMessage> Dispatch(HttpRequestMessage req)
    {
        req.Headers.TryAddWithoutValidation("accept-language", L10n.DeviceLanguage());
        if (_tenantKey is not null)
            req.Headers.TryAddWithoutValidation("x-tenant-key", _tenantKey);
        return _http.SendAsync(req);
    }

    /// <summary>The customer-managed key, for a tenant that holds its own.
    ///
    /// <para><c>_tenant</c> on the backend reads <c>x-tenant-key</c>, and a
    /// vault under customer custody answers <b>428</b> to every record read
    /// and every write without it. No shell sent it, so a tenant that pressed
    /// <i>hold our own key</i> in the console had locked all three phones out
    /// of the vault.</para>
    ///
    /// <para>In memory, never in settings or the credential store: the whole
    /// promise of this custody mode is that the key exists only where the
    /// customer puts it. Being asked again after a relaunch is that promise
    /// working.</para></summary>
    private string? _tenantKey;

    public void HoldKey(string? key)
    {
        var t = key?.Trim();
        _tenantKey = string.IsNullOrEmpty(t) ? null : t;
    }

    public void SetBase(string url)
    {
        var t = url.TrimEnd('/');
        if (!string.IsNullOrWhiteSpace(t)) _http.BaseAddress = new Uri(t);
    }


    /// <summary>What the deployment can and cannot reach. Read-only: the
    /// posture is set in the deployment's environment, not in the app.</summary>
    public async Task<OfflinePosture> OfflineStatus() =>
        await Send<OfflinePosture>(new HttpRequestMessage(HttpMethod.Get,
            "/offline/status"));

    /// <param name="token">Empty for the public routes — the posture read
    /// is one of them, and a bearer header with nothing behind it is a
    /// worse answer than no header at all.</param>
    public record ProblemRow(
        [property: JsonPropertyName("source")] string Source,
        [property: JsonPropertyName("app_version")] string AppVersion,
        [property: JsonPropertyName("platform")] string Platform,
        [property: JsonPropertyName("op")] string Op,
        [property: JsonPropertyName("status_code")] int StatusCode,
        [property: JsonPropertyName("day")] string Day,
        [property: JsonPropertyName("count")] int Count);
    public record ProblemRowsResponse(
        [property: JsonPropertyName("rows")] ProblemRow[] Rows);

    // The failure aggregate this backend keeps. Reading is the operator's:
    // PDI_PROBLEMS_KEY as the token, or nothing when asking from the machine
    // the backend runs on.
    public Task<ProblemRowsResponse> ProblemRows(string key = "") =>
        Send<ProblemRowsResponse>(
            new HttpRequestMessage(HttpMethod.Get, "/v1/problems"), key);

    private async Task<T> Send<T>(HttpRequestMessage req, string token = "")
    {
        if (!string.IsNullOrWhiteSpace(token))
            req.Headers.Add("authorization", $"Bearer {token}");
        // The path as written, for the recorder. Read before the send, which
        // consumes `req`. Absolute and relative are both handled: these calls
        // build relative URIs against BaseAddress, but a `RequestUri` that
        // ever arrived absolute would otherwise put the host in the log —
        // not private, but not the operation either.
        var method = req.Method.Method;
        var path = req.RequestUri is { IsAbsoluteUri: true } abs
            ? abs.AbsolutePath
            : req.RequestUri?.ToString() ?? "";

        // The language the reader actually speaks. Every sentence the backend
        // composes on a public route is chosen from this header, and no native
        // shell was sending it.

        HttpResponseMessage res;
        try
        {
            res = await Dispatch(req);
        }
        catch
        {
            // Never reached a server. Recorded as status 0; the thrown error
            // still carries its message to the person, who owns it.
            Problems.Record(method, path, 0);
            throw;
        }
        var body = await res.Content.ReadAsStringAsync();
        if (!res.IsSuccessStatusCode)
        {
            // The status and the operation, never the detail below: these
            // messages quote what the person typed, which is theirs to read
            // and nobody's to keep.
            Problems.Record(method, path, (int)res.StatusCode);
            // GetString() throws on an array, which a 422's `detail` is, so the
            // catch swallowed it and the person saw the status code. `message`
            // is the sentence the backend composes beside the rows.
            string? said = null;
            try
            {
                var root = JsonDocument.Parse(body).RootElement;
                if (root.TryGetProperty("message", out var m) && m.ValueKind == JsonValueKind.String)
                    said = m.GetString();
                else if (root.TryGetProperty("detail", out var d) && d.ValueKind == JsonValueKind.String)
                    said = d.GetString();
            }
            catch { /* non-JSON error body */ }
            throw new HttpRequestException(said ?? $"HTTP {(int)res.StatusCode}");
        }
        return JsonSerializer.Deserialize<T>(string.IsNullOrEmpty(body) ? "{}" : body)!;
    }

    private async Task SendNoContent(HttpRequestMessage req, string token)
    {
        req.Headers.Add("authorization", $"Bearer {token}");
        var res = await Dispatch(req);
        if (!res.IsSuccessStatusCode)
        {
            var body = await res.Content.ReadAsStringAsync();
            // GetString() throws on an array, which a 422's `detail` is, so the
            // catch swallowed it and the person saw the status code. `message`
            // is the sentence the backend composes beside the rows.
            string? said = null;
            try
            {
                var root = JsonDocument.Parse(body).RootElement;
                if (root.TryGetProperty("message", out var m) && m.ValueKind == JsonValueKind.String)
                    said = m.GetString();
                else if (root.TryGetProperty("detail", out var d) && d.ValueKind == JsonValueKind.String)
                    said = d.GetString();
            }
            catch { /* ignore */ }
            throw new HttpRequestException(said ?? $"HTTP {(int)res.StatusCode}");
        }
    }

    /// <summary>List record keys — also the sign-in validation call.</summary>
    public async Task<string[]> Keys(string token) =>
        (await Send<KeysResponse>(new HttpRequestMessage(HttpMethod.Get, "/records"), token)).Keys;

    /// <summary>Everything this deployment holds about the tenant, by table.
    ///
    /// <para>Distinct from the disaster-recovery snapshot, which is
    /// ciphertext and exists to be restored. This is the portability answer:
    /// what do you have about us.</para></summary>
    public Task<TenantExport> ExportEverything(string token) =>
        Send<TenantExport>(new HttpRequestMessage(
            HttpMethod.Get, "/export"), token);

    public Task<RecordProvenance> Provenance(string token, string key) =>
        Send<RecordProvenance>(new HttpRequestMessage(
            HttpMethod.Get, $"/provenance/{key}"), token);

    // ---- exchange details: one transfer, one intake, their chains ----

    public Task<Transfer> TransferOne(string token, string tid) =>
        Send<Transfer>(new HttpRequestMessage(HttpMethod.Get,
            $"/transfers/{tid}"), token);

    public Task<CustodyChainOut> TransferCustody(string token, string tid) =>
        Send<CustodyChainOut>(new HttpRequestMessage(HttpMethod.Get,
            $"/transfers/{tid}/custody"), token);

    // The recipient's act — the one-shot receive token is the whole
    // credential, riding as its own header the way the submit does.
    public Task<ReceivedFileOut> ReceiveTransfer(string tid, string receiveToken)
    {
        var req = new HttpRequestMessage(HttpMethod.Post,
            $"/transfers/{tid}/receive");
        req.Headers.TryAddWithoutValidation("x-receive-token", receiveToken);
        return Send<ReceivedFileOut>(req);
    }

    public Task<Intake> IntakeOne(string token, string iid) =>
        Send<Intake>(new HttpRequestMessage(HttpMethod.Get,
            $"/intakes/{iid}"), token);

    public Task<CustodyChainOut> IntakeCustody(string token, string iid) =>
        Send<CustodyChainOut>(new HttpRequestMessage(HttpMethod.Get,
            $"/intakes/{iid}/custody"), token);

    // ---- positions: the assistant builder ----

    public async Task<string> BuildPosition(string token, string industry,
                                            string jobTitle)
    {
        var made = await Send<BlueprintOut>(
            new HttpRequestMessage(HttpMethod.Post, "/positions")
            {
                Content = JsonContent.Create(new
                {
                    industry,
                    role = new { job_title = jobTitle },
                }),
            }, token);
        return $"{made.Id} · {made.Industry}";
    }

    public Task<PositionsListOut> ListPositions(string token) =>
        Send<PositionsListOut>(new HttpRequestMessage(HttpMethod.Get,
            "/positions"), token);

    public async Task<string> GetPosition(string token, string id)
    {
        var b = await Send<BlueprintOut>(new HttpRequestMessage(HttpMethod.Get,
            $"/positions/{id}"), token);
        return $"{b.Id} · {b.Industry}";
    }

    // ---- posture: where the vault lives, and whether it is up ----

    public Task<HealthOut> Health() =>
        Send<HealthOut>(new HttpRequestMessage(HttpMethod.Get, "/health"));

    public Task<HostingModesOut> HostingModes() =>
        Send<HostingModesOut>(new HttpRequestMessage(HttpMethod.Get, "/hosting"));

    public Task<HostingModeOut> Hosting(string token, string tid) =>
        Send<HostingModeOut>(new HttpRequestMessage(HttpMethod.Get,
            $"/hosting/{tid}"), token);

    public async Task<int> HostingHistory(string token, string tid) =>
        (await Send<HostingHistoryOut>(new HttpRequestMessage(HttpMethod.Get,
            $"/hosting/{tid}/history"), token)).History.Length;

    public Task<OkOut> SetHosting(string token, string tid, string mode) =>
        Send<OkOut>(new HttpRequestMessage(HttpMethod.Put, $"/hosting/{tid}")
        {
            Content = JsonContent.Create(new { mode }),
        }, token);

    public Task<OkOut> RecordDeployment(string token) =>
        Send<OkOut>(new HttpRequestMessage(HttpMethod.Post, "/deployments")
        {
            Content = JsonContent.Create(new { name = "new site", option = "colocation" }),
        }, token);

    public async Task<int> Operations(string token) =>
        (await Send<OperationsOut>(new HttpRequestMessage(HttpMethod.Get,
            "/operations"), token)).Entries.Length;

    public async Task<string> AuditSchema()
    {
        var s = await Send<AuditSchemaOut>(new HttpRequestMessage(
            HttpMethod.Get, "/audit/schema"));
        return $"{s.Actions.Length} · {s.Retention}";
    }

    // The tenant's own standing, which is a smaller shape than the
    // operator's BAA record: names live on the admin route only.
    public Task<BaaStandingOut> BaaStatus(string token) =>
        Send<BaaStandingOut>(new HttpRequestMessage(HttpMethod.Get, "/baa"), token);

    // ---- continuity: bequests, and what outlives the tenant ----

    public Task<BequestRow[]> Bequests(string token) =>
        Send<BequestRow[]>(new HttpRequestMessage(HttpMethod.Get, "/bequests"), token);

    public Task<BequestRow> CreateBequest(string token, string grantee,
                                          string[] prefixes, string? note) =>
        Send<BequestRow>(new HttpRequestMessage(HttpMethod.Post, "/bequests")
        {
            Content = JsonContent.Create(new
            {
                grantee_name = grantee,
                key_prefixes = prefixes,
                note,
            }),
        }, token);

    public Task<BequestRow> RevokeBequest(string token, string bid) =>
        Send<BequestRow>(new HttpRequestMessage(HttpMethod.Delete,
            $"/bequests/{bid}"), token);

    // The executor's act: activation attests the condition — the reference
    // goes into the audit chain — and mints the grant token, shown once.
    public Task<BequestRow> ActivateBequest(string adminToken, string bid,
                                            string activationRef) =>
        Send<BequestRow>(new HttpRequestMessage(HttpMethod.Post,
            $"/bequests/{bid}/activate")
        {
            Content = JsonContent.Create(new { activation_ref = activationRef }),
        }, adminToken);

    public Task<RevokedOut> RevokeBequestGrant(string adminToken, string bid) =>
        Send<RevokedOut>(new HttpRequestMessage(HttpMethod.Delete,
            $"/bequests/{bid}/grant"), adminToken);

    // The heir's side. Two separate secrets on purpose — the grant token
    // says the condition was attested, the customer key decrypts — so both
    // ride as headers on the request itself.
    public Task<KeysListOut> BequestKeys(string grantToken, string customerKey)
    {
        var req = new HttpRequestMessage(HttpMethod.Get, "/bequests/grant/keys");
        req.Headers.TryAddWithoutValidation("x-grant-token", grantToken);
        req.Headers.TryAddWithoutValidation("x-tenant-key", customerKey);
        return Send<KeysListOut>(req);
    }

    public async Task<string> BequestRead(string key, string grantToken,
                                          string customerKey)
    {
        var req = new HttpRequestMessage(HttpMethod.Get,
            $"/bequests/grant/read?key={Uri.EscapeDataString(key)}");
        req.Headers.TryAddWithoutValidation("x-grant-token", grantToken);
        req.Headers.TryAddWithoutValidation("x-tenant-key", customerKey);
        var res = await Dispatch(req);
        return await res.Content.ReadAsStringAsync();
    }

    // ---- contributions, the snapshot, and the custody ops ----

    public async Task<int> Contributions(string token) =>
        (await Send<ContribCount>(new HttpRequestMessage(HttpMethod.Get,
            "/contributions"), token)).Count;

    public async Task<string> Contribute(string token, string source,
                                         string? reference)
    {
        var made = await Send<ContribOut>(
            new HttpRequestMessage(HttpMethod.Post, "/contributions")
            {
                Content = JsonContent.Create(new
                {
                    source,
                    kind = "outcome",
                    payload = new { helped = true },
                    @ref = reference,
                }),
            }, token);
        return made.Key;
    }

    public Task<OkOut> WithdrawContribution(string token, string reference) =>
        Send<OkOut>(new HttpRequestMessage(HttpMethod.Delete,
            $"/contributions/{reference}"), token);

    // The whole tenant, in hand — raw on purpose: records are arbitrary
    // JSON and the door is the fetch, not a schema. Held so a restore can
    // put back exactly what was taken.
    private System.Text.Json.JsonElement? _lastSnapshot;

    public async Task<int> SnapshotRecords(string token)
    {
        var req = new HttpRequestMessage(HttpMethod.Get, "/snapshot");
        req.Headers.Add("authorization", $"Bearer {token}");
        var res = await Dispatch(req);
        var doc = System.Text.Json.JsonDocument.Parse(
            await res.Content.ReadAsStringAsync());
        _lastSnapshot = doc.RootElement.TryGetProperty("records", out var records)
            ? records.Clone() : null;
        return _lastSnapshot?.GetArrayLength() ?? 0;
    }

    public Task<OkOut> RestoreSnapshot(string token) =>
        Send<OkOut>(new HttpRequestMessage(HttpMethod.Post, "/restore")
        {
            Content = JsonContent.Create(new { records = _lastSnapshot }),
        }, token);

    public async Task<string> RetentionPolicy(string adminToken) =>
        (await Send<RetentionPolicyOut>(new HttpRequestMessage(HttpMethod.Get,
            "/retention"), adminToken)).RecoveryWindow;

    public async Task<string> RetentionSweep(string adminToken)
    {
        var s = await Send<SweepOut>(new HttpRequestMessage(HttpMethod.Post,
            "/retention/sweep"), adminToken);
        return $"{s.PurgedTenants} · {s.ExpiredRecords} · {s.RecoveryWindow}";
    }

    public Task<OkOut> SeedDemo(string adminToken) =>
        Send<OkOut>(new HttpRequestMessage(HttpMethod.Post, "/seed"), adminToken);

    // ---- tenants: the operator's half ----

    public Task<TenantMade> CreateTenant(string adminToken, string name) =>
        Send<TenantMade>(new HttpRequestMessage(HttpMethod.Post, "/tenants")
        {
            Content = JsonContent.Create(new { name }),
        }, adminToken);

    public Task<OkOut> RestoreTenant(string adminToken, string tid) =>
        Send<OkOut>(new HttpRequestMessage(HttpMethod.Post,
            $"/tenants/{tid}/restore"), adminToken);

    // `mode` decides whether the tenant can come back. The audit trail
    // survives either way — that is the point of a hash chain.
    public Task<OkOut> DeleteTenant(string adminToken, string tid, string mode) =>
        Send<OkOut>(new HttpRequestMessage(HttpMethod.Delete,
            $"/tenants/{tid}?mode={mode}"), adminToken);

    public Task<MintedTokenOut> MintTenantToken(string adminToken, string tid,
                                                string role) =>
        Send<MintedTokenOut>(new HttpRequestMessage(HttpMethod.Post,
            $"/tenants/{tid}/tokens")
        {
            Content = JsonContent.Create(new { role }),
        }, adminToken);

    public Task<RetentionOut> SetTenantRetention(string adminToken, string tid,
                                                 string retention) =>
        Send<RetentionOut>(new HttpRequestMessage(HttpMethod.Put,
            $"/tenants/{tid}/retention")
        {
            Content = JsonContent.Create(new { retention }),
        }, adminToken);

    public Task<BaaOut> TenantBaa(string adminToken, string tid) =>
        Send<BaaOut>(new HttpRequestMessage(HttpMethod.Get,
            $"/tenants/{tid}/baa"), adminToken);

    public Task<BaaOut> RecordTenantBaa(string adminToken, string tid,
                                        string customer, string operatorName,
                                        string date) =>
        Send<BaaOut>(new HttpRequestMessage(HttpMethod.Post,
            $"/tenants/{tid}/baa")
        {
            Content = JsonContent.Create(new
            {
                customer_legal_name = customer,
                operator_legal_name = operatorName,
                effective_date = date,
            }),
        }, adminToken);

    public Task<OkOut> RescindTenantBaa(string adminToken, string tid) =>
        Send<OkOut>(new HttpRequestMessage(HttpMethod.Delete,
            $"/tenants/{tid}/baa"), adminToken);

    // ---- the agent at the gate ----

    public Task<GateCeilingOut> GateCeiling(string token) =>
        Send<GateCeilingOut>(new HttpRequestMessage(HttpMethod.Get, "/gate/ceiling"), token);

    public Task<GateChannelOut> GateChannel(string token) =>
        Send<GateChannelOut>(new HttpRequestMessage(HttpMethod.Get, "/gate/channel"), token);

    public Task<GateRosterOut> GateRoster(string token) =>
        Send<GateRosterOut>(new HttpRequestMessage(HttpMethod.Get, "/gate/roster"), token);

    public Task<RosterEntryOut> AddToRoster(string token, string name, string role) =>
        Send<RosterEntryOut>(new HttpRequestMessage(HttpMethod.Post, "/gate/roster")
        {
            Content = JsonContent.Create(new { name, role }),
        }, token);

    public Task<RemovedOut> RemoveFromRoster(string token, string rid) =>
        Send<RemovedOut>(new HttpRequestMessage(HttpMethod.Delete,
            $"/gate/roster/{rid}"), token);

    public Task<TzOut> SetGateTimezone(string token, string timezone) =>
        Send<TzOut>(new HttpRequestMessage(HttpMethod.Put, "/gate/timezone")
        {
            Content = JsonContent.Create(new { timezone }),
        }, token);

    public Task<GatePageOut[]> GatePages(string token) =>
        Send<GatePageOut[]>(new HttpRequestMessage(HttpMethod.Get, "/gate/pages"), token);

    public Task<GatePageOut> RetryGatePage(string token, string pid) =>
        Send<GatePageOut>(new HttpRequestMessage(HttpMethod.Post,
            $"/gate/pages/{pid}/retry"), token);

    // ---- carriers: custody codes on sealed things ----

    public Task<CarrierBeacon[]> CarrierBeacons(string token) =>
        Send<CarrierBeacon[]>(new HttpRequestMessage(HttpMethod.Get, "/beacons"), token);

    public Task<CarrierBeacon> PlaceCarrierBeacon(string token, string label,
                                                  string disclose) =>
        Send<CarrierBeacon>(new HttpRequestMessage(HttpMethod.Post, "/beacons")
        {
            Content = JsonContent.Create(new { ref_kind = "object", label, disclose }),
        }, token);

    public Task<CarrierBeacon> CarrierBeacon(string token, string bid) =>
        Send<CarrierBeacon>(new HttpRequestMessage(HttpMethod.Get, $"/beacons/{bid}"), token);

    public Task<CarrierBeacon> SetCarrierState(string token, string bid, string state) =>
        Send<CarrierBeacon>(new HttpRequestMessage(HttpMethod.Put, $"/beacons/{bid}/state")
        {
            Content = JsonContent.Create(new { state }),
        }, token);

    public Task<LiftedOut> LiftCarrierBeacon(string token, string bid) =>
        Send<LiftedOut>(new HttpRequestMessage(HttpMethod.Delete, $"/beacons/{bid}"), token);

    public Task<CustodyChainOut> CarrierCustody(string token, string bid) =>
        Send<CustodyChainOut>(new HttpRequestMessage(HttpMethod.Get, $"/beacons/{bid}/custody"), token);

    // The scanner's half — no bearer at all: the code in the hand is the
    // whole credential, and what it earns is capped by `disclose`.
    public Task<ScanCardOut> ScanCard(string bid) =>
        Send<ScanCardOut>(new HttpRequestMessage(HttpMethod.Get, $"/s/{bid}/card"));

    // The landing page and its QR image: the JSON sender cannot carry
    // either, so the door is the request the opener makes, and building it
    // here is what the route audit reads.
    public string ScanPageUrl(string bid) =>
        new Uri(_http.BaseAddress!,
                new HttpRequestMessage(HttpMethod.Get, $"/s/{bid}").RequestUri!).ToString();

    public string ScanQrUrl(string bid) =>
        new Uri(_http.BaseAddress!,
                new HttpRequestMessage(HttpMethod.Get, $"/s/{bid}/qr.svg").RequestUri!).ToString();

    public Task<FoundAckOut> ReportFound(string bid) =>
        Send<FoundAckOut>(new HttpRequestMessage(HttpMethod.Post, $"/s/{bid}/found")
        {
            Content = JsonContent.Create(new { where = "loading dock" }),
        });

    public Task<RingRowOut> RingHolder(string bid) =>
        Send<RingRowOut>(new HttpRequestMessage(HttpMethod.Post, $"/s/{bid}/ring")
        {
            Content = JsonContent.Create(new { kind = "delivery" }),
        });

    public Task<RingRowOut[]> Rings(string token) =>
        Send<RingRowOut[]>(new HttpRequestMessage(HttpMethod.Get, "/rings"), token);

    public Task<RingRowOut> RingTranscript(string token, string rid) =>
        Send<RingRowOut>(new HttpRequestMessage(HttpMethod.Get, $"/rings/{rid}/transcript"), token);

    // Resolve the recipient's page before the link goes into an email — a
    // misconfigured public base is otherwise discovered by the recipient,
    // who has nobody to ask.
    public async Task<bool> CheckRecipientPage(string tid)
    {
        var req = new HttpRequestMessage(HttpMethod.Get, $"/r/{tid}");
        var path = req.RequestUri!.ToString();
        var res = await Dispatch(req);
        if (!res.IsSuccessStatusCode)
            Problems.Record("GET", path, (int)res.StatusCode);
        return res.IsSuccessStatusCode;
    }

    // How to open this console on a phone: same Wi-Fi, no app store.
    public Task<PairInfoOut> PairInfo() =>
        Send<PairInfoOut>(new HttpRequestMessage(HttpMethod.Get, "/pair"));

    public string PairQrUrl() =>
        new Uri(_http.BaseAddress!,
                new HttpRequestMessage(HttpMethod.Get, "/pair/qr.svg").RequestUri!).ToString();

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

    // -- admin: key management (PDI_ADMIN_TOKEN, never the tenant token) --

    public Task<KeysInfo> AdminKeys(string adminToken) =>
        Send<KeysInfo>(new HttpRequestMessage(HttpMethod.Get, "/keys"), adminToken);

    public async Task<KeysInfo> RotateKey(string adminToken)
    {
        // Server default reseals every record immediately.
        var req = new HttpRequestMessage(HttpMethod.Post, "/keys/rotate")
        {
            Content = JsonContent.Create(new { }),
        };
        req.Headers.Add("authorization", $"Bearer {adminToken}");
        var res = await Dispatch(req);
        res.EnsureSuccessStatusCode();
        return await AdminKeys(adminToken);
    }

    public Task<RetireResult> RetireKeys(string adminToken) =>
        Send<RetireResult>(new HttpRequestMessage(HttpMethod.Post, "/keys/retire")
        {
            Content = JsonContent.Create(new { }),
        }, adminToken);

    public Task<VerifyResult> AuditVerify(string token) =>
        Send<VerifyResult>(new HttpRequestMessage(HttpMethod.Get, "/audit/verify"), token);

    public Task<AuditEntry[]> AuditEntries(string token) =>
        Send<AuditEntry[]>(new HttpRequestMessage(HttpMethod.Get, "/audit"), token);

    // -- Help us improve — product feedback --

    public async Task SubmitImprovement(string token, string category,
                                        string message, int? rating)
    {
        object body = rating is { } r
            ? new { category, message, rating = r }
            : new { category, message };
        var req = new HttpRequestMessage(HttpMethod.Post, "/improve")
        {
            Content = JsonContent.Create(body),
        };
        await SendNoContent(req, token);
    }

    public Task<ImproveState> Improvements(string token) =>
        Send<ImproveState>(new HttpRequestMessage(HttpMethod.Get, "/improve"), token);

    // The accessibility door: tokenless on purpose — reporting that the
    // vault shut you out must not require the tenant token it may have
    // shut you out of. The words stay on the deployment.
    public async Task<string> SendAccessReport(string doing, string wall,
                                               string? help, string lang)
    {
        object body = help is { Length: > 0 } h
            ? new { doing, wall, help = h, lang }
            : new { doing, wall, lang };
        var req = new HttpRequestMessage(HttpMethod.Post, "/access/reports")
        {
            Content = JsonContent.Create(body),
        };
        await Send<AccessReceipt>(req);
        return "received";
    }

    // Admin-token read — the deployment's operator, never a tenant.
    public Task<AccessReportsState> AccessReports(string adminToken) =>
        Send<AccessReportsState>(
            new HttpRequestMessage(HttpMethod.Get, "/access/reports"), adminToken);

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

    public Task ConnectorScrape(string token, string cid)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, $"/connectors/{cid}/scrape");
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
        var res = await Dispatch(req);
        if (!res.IsSuccessStatusCode)
        {
            var body = await res.Content.ReadAsStringAsync();
            // GetString() throws on an array, which a 422's `detail` is, so the
            // catch swallowed it and the person saw the status code. `message`
            // is the sentence the backend composes beside the rows.
            string? said = null;
            try
            {
                var root = JsonDocument.Parse(body).RootElement;
                if (root.TryGetProperty("message", out var m) && m.ValueKind == JsonValueKind.String)
                    said = m.GetString();
                else if (root.TryGetProperty("detail", out var d) && d.ValueKind == JsonValueKind.String)
                    said = d.GetString();
            }
            catch { /* ignore */ }
            throw new HttpRequestException(said ?? $"HTTP {(int)res.StatusCode}");
        }
    }
}

public record OfflinePosture(
    [property: JsonPropertyName("offline")] bool Offline,
    [property: JsonPropertyName("external_transmission_possible")] bool ExternalTransmissionPossible,
    [property: JsonPropertyName("local_destinations_allowed")] string LocalDestinationsAllowed,
    [property: JsonPropertyName("guarantees")] string[] Guarantees);
