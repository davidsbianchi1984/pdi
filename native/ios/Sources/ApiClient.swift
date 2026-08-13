import Foundation

// MARK: - Wire models (mirror pdi/api.py)

struct KeysResponse: Decodable { let keys: [String] }
struct VaultRecord: Decodable { let key: String; let value: String; let updated_at: String? }

struct SealedInfo: Decodable {
    let cipher: String
    let bound_to: String
    let created_at: String
    let updated_at: String
    let ciphertext_bytes: Int
}

struct ProvenanceEvent: Decodable { let action: String; let at: String }
struct ProvenanceAudit: Decodable { let events: [ProvenanceEvent]; let count: Int }
struct ChainState: Decodable { let intact: Bool }

struct RecordProvenance: Decodable {
    let key: String
    let origin: String
    let sealed: SealedInfo
    let audit: ProvenanceAudit
    let chain: ChainState
    let note: String
}

struct LanguageInfo: Decodable {
    let code: String
    let label: String
    let notes_translated: Bool?
}

struct LanguagesList: Decodable {
    let languages: [LanguageInfo]
    let defaultCode: String
    enum CodingKeys: String, CodingKey {
        case languages
        case defaultCode = "default"
    }
}

struct LanguageChoice: Decodable { let language: String; let label: String; let mode: String? }
struct VerifyResult: Decodable { let intact: Bool }
struct AuditEntry: Decodable {
    let seq: Int
    let action: String
    let ref: String?
    let at: String
    let category: String?
}

struct RobotSpec: Decodable {
    let model: String
    let label: String
    let maker: String
    let kind: String
}

struct RoboticsCatalog: Decodable {
    let robots: [RobotSpec]
    let data_kinds: [String]
}

struct Robot: Decodable {
    let id: String
    let model: String
    let name: String
    let status: String?
    let collected: Int?
}

struct IngestResult: Decodable { let sealed: Bool; let key: String }
struct RobotData: Decodable { let keys: [String] }

struct ComplianceProgram: Decodable { let key: String; let label: String }
struct CompliancePrograms: Decodable { let programs: [ComplianceProgram] }

struct Transfer: Decodable {
    let id: String
    let recipient: String
    let filename: String
    let status: String
    let programs: [String]
    let retention_days: Int?
    let expires_at: String?
    let receive_token: String?     // present only on creation — shown once
}

struct Intake: Decodable {
    let id: String
    let from_party: String
    let purpose: String?
    let status: String
    let programs: [String]
    let filename: String?
    let submit_token: String?      // present only on creation — shown once
}

struct IntakeFile: Decodable {
    let filename: String?
    let content: String?
}

struct SocialConn: Decodable {
    let id: String
    let platform: String
    let direction: String
    let handle: String?
    let status: String?
}

struct ImproveReceipt: Decodable { let id: String; let status: String }

struct ImproveItem: Decodable, Identifiable {
    let id: String
    let category: String
    let message: String
    let status: String
}

struct ImproveState: Decodable {
    let mine: [ImproveItem]
    let tally: [String: Int]
    let total: Int
}

struct AccessReceipt: Decodable { let id: String; let status: String; let note: String? }
struct AccessReportRow: Decodable, Identifiable {
    let id: String; let lang: String; let doing: String; let wall: String
    let help: String?; let status: String; let created_at: String
}
struct AccessReportsState: Decodable { let reports: [AccessReportRow]; let total: Int }

struct KeyVersion: Decodable, Identifiable {
    let version: Int
    let active: Bool
    let created_at: String?
    var id: Int { version }
}

struct TenantExport: Decodable {
    let tables: [String: [[String: AnyCodableValue]]]
    let note: String
}

/// A JSON value the export carries whose shape this shell does not model —
/// it counts rows and shows the table names; reading every column of every
/// table into Swift types would be a second copy of the schema.
struct AnyCodableValue: Decodable {
    init(from decoder: Decoder) throws { }
}

struct KeysInfo: Decodable { let provider: String; let versions: [KeyVersion] }

struct RetireResult: Decodable { let retired: Int; let versions: [KeyVersion] }

// MARK: - Client

enum ApiError: LocalizedError {
    case http(String)
    var errorDescription: String? { if case let .http(m) = self { return m }; return nil }
}

/// Async client for the PDI vault backend. Every call carries the tenant bearer
/// token (`pdi_...`); the token is issued out of band and pasted at sign-in.
actor ApiClient {
    static let shared = ApiClient()
    var base = URL(string: "http://127.0.0.1:8000")!

    func setBase(_ s: String) {
        let t = s.hasSuffix("/") ? String(s.dropLast()) : s
        if !t.isEmpty, let u = URL(string: t) { base = u }
    }

    /// The customer-managed key, for a tenant that holds its own.
    ///
    /// `_tenant` on the backend reads `x-tenant-key`, and a vault under
    /// customer custody answers **428** to every record read and every write
    /// without it. No shell sent it, so a tenant that pressed *hold our own
    /// key* in the console had locked all three phones out of the vault.
    ///
    /// In memory, never in `UserDefaults` or the keychain: the whole promise
    /// of this custody mode is that the key exists only where the customer
    /// puts it. Being asked again after a relaunch is that promise working.
    private var tenantKey: String?

    func holdKey(_ key: String?) {
        let t = key?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        tenantKey = t.isEmpty ? nil : t
    }

    // token is optional because GET /languages is genuinely public — it is
    // the catalog a client reads before it has a tenant token at all. Sending
    // an empty "Bearer " there would be a malformed header, not a no-op.

    /// Read-only on purpose: the posture is set in the deployment's
    /// environment, not by somebody signed into the app.
    func offlineStatus() async throws -> OfflinePosture {
        try await request("/offline/status")
    }


    struct ProblemRow: Decodable {
        let source: String
        let app_version: String
        let platform: String
        let op: String
        let status_code: Int
        let day: String
        let count: Int
    }
    struct ProblemRows: Decodable { let rows: [ProblemRow] }

    /// The failure aggregate this backend keeps. Reading is the operator's:
    /// the problems key as the token, or nothing when asking from the
    /// machine the backend runs on.
    func problemRows(key: String) async throws -> ProblemRows {
        try await request("/v1/problems", token: key)
    }

    private func request<T: Decodable>(_ path: String, method: String = "GET",
                                       body: [String: Any]? = nil,
                                       token: String? = nil) async throws -> T {
        var req = URLRequest(url: base.appendingPathComponent(path))
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "content-type")
        // The language the reader actually speaks. Every sentence the
        // backend composes on a public route is chosen from this header,
        // and no native shell was sending it — the browser sends it for
        // free, which is why the phones were the ones still answering in
        // English after the routes learned to speak.
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        if let token { req.setValue("Bearer \(token)", forHTTPHeaderField: "authorization") }
        if let tenantKey { req.setValue(tenantKey, forHTTPHeaderField: "x-tenant-key") }
        if let body { req.httpBody = try JSONSerialization.data(withJSONObject: body) }

        let data: Data
        let resp: URLResponse
        do {
            (data, resp) = try await URLSession.shared.data(for: req)
        } catch {
            // Never reached a server. Recorded as status 0; the thrown error
            // still carries its message to the person, who owns it.
            Problems.record(method: method, path: path, status: 0)
            throw error
        }
        guard let http = resp as? HTTPURLResponse else {
            Problems.record(method: method, path: path, status: 0)
            throw ApiError.http("No response")
        }
        guard (200..<300).contains(http.statusCode) else {
            // The status and the operation, never the detail below: these
            // messages quote what the person typed, which is theirs to read
            // and nobody's to keep.
            Problems.record(method: method, path: path, status: http.statusCode)
            // A 422 answers with a *list* of rows, not a string, so `as? String`
            // gave nil and the person saw the status code — less than they saw
            // before their language was ever considered. `message` is the
            // sentence the backend composes beside the rows; read it first.
            let body = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
            let said = (body?["message"] as? String) ?? (body?["detail"] as? String)
            throw ApiError.http(said ?? "HTTP \(http.statusCode)")
        }
        if data.isEmpty { return try JSONDecoder().decode(T.self, from: Data("{}".utf8)) }
        return try JSONDecoder().decode(T.self, from: data)
    }

    /// Everything this deployment holds about the tenant, by table.
    ///
    /// Distinct from the disaster-recovery snapshot: that one is ciphertext
    /// and exists to be restored. This is the portability answer, and the
    /// phone needs it because a person whose only device is a phone is
    /// exactly the person who cannot use a desktop console to get their
    /// data out.
    func exportEverything(token: String) async throws -> TenantExport {
        try await request("/export", token: token)
    }

    /// List the tenant's record keys — also the sign-in validation call.
    func keys(token: String) async throws -> [String] {
        let r: KeysResponse = try await request("/records", token: token)
        return r.keys
    }

    func record(token: String, key: String) async throws -> VaultRecord {
        try await request("/records/\(key)", token: token)
    }

    func putRecord(token: String, key: String, value: String) async throws {
        struct Ok: Decodable {}
        let _: Ok = try await request("/records", method: "PUT",
                                      body: ["key": key, "value": value], token: token)
    }

    func deleteRecord(token: String, key: String) async throws {
        struct Ok: Decodable {}
        let _: Ok = try await request("/records/\(key)", method: "DELETE", token: token)
    }

    func provenance(token: String, key: String) async throws -> RecordProvenance {
        try await request("/provenance/\(key)", token: token)
    }

    func languages() async throws -> LanguagesList { try await request("/languages") }

    func language(token: String) async throws -> LanguageChoice {
        try await request("/language", token: token)
    }

    func setLanguage(token: String, code: String,
                     mode: String = "pre") async throws -> LanguageChoice {
        try await request("/language", method: "PUT",
                          body: ["language": code, "mode": mode], token: token)
    }

    // MARK: Help us improve — product feedback

    func submitImprovement(token: String, category: String, message: String,
                           rating: Int?) async throws -> ImproveReceipt {
        var body: [String: Any] = ["category": category, "message": message]
        if let rating { body["rating"] = rating }
        return try await request("/improve", method: "POST", body: body, token: token)
    }

    func improvements(token: String) async throws -> ImproveState {
        try await request("/improve", token: token)
    }

    /// The accessibility door: tokenless on purpose — reporting that the
    /// vault shut you out must not require the tenant token it may have
    /// shut you out of. The words stay on the deployment.
    func sendAccessReport(doing: String, wall: String, help: String?,
                          lang: String) async throws -> AccessReceipt {
        var body: [String: Any] = ["doing": doing, "wall": wall, "lang": lang]
        if let help, !help.isEmpty { body["help"] = help }
        return try await request("/access/reports", method: "POST", body: body)
    }

    /// Admin-token read — the deployment's operator, never a tenant.
    func accessReports(adminToken: String) async throws -> AccessReportsState {
        try await request("/access/reports", token: adminToken)
    }

    // MARK: Admin — key management (PDI_ADMIN_TOKEN, never the tenant token)

    func adminKeys(adminToken: String) async throws -> KeysInfo {
        try await request("/keys", token: adminToken)
    }

    func rotateKey(adminToken: String) async throws -> KeysInfo {
        // Server default reseals every record immediately, so nothing is
        // ever left on a stale key version.
        struct Ok: Decodable {}
        let _: Ok = try await request("/keys/rotate", method: "POST",
                                      token: adminToken)
        return try await adminKeys(adminToken: adminToken)
    }

    func retireKeys(adminToken: String) async throws -> RetireResult {
        try await request("/keys/retire", method: "POST", token: adminToken)
    }

    func auditVerify(token: String) async throws -> VerifyResult {
        try await request("/audit/verify", token: token)
    }

    func auditEntries(token: String) async throws -> [AuditEntry] {
        try await request("/audit", token: token)
    }

    // MARK: Robots as vault-backed data sources

    func roboticsCatalog(token: String) async throws -> RoboticsCatalog {
        try await request("/robotics/catalog", token: token)
    }

    func robots(token: String) async throws -> [Robot] {
        try await request("/robots", token: token)
    }

    func bindRobot(token: String, model: String) async throws -> Robot {
        try await request("/robots", method: "POST",
                          body: ["model": model], token: token)
    }

    func ingest(token: String, rid: String, kind: String,
                content: String) async throws -> IngestResult {
        try await request("/robots/\(rid)/ingest", method: "POST",
                          body: ["kind": kind, "content": content], token: token)
    }

    func robotData(token: String, rid: String) async throws -> RobotData {
        try await request("/robots/\(rid)/data", token: token)
    }

    // MARK: Compliance-grade secure transfers

    func compliancePrograms(token: String) async throws -> CompliancePrograms {
        try await request("/compliance/programs", token: token)
    }

    func transfers(token: String) async throws -> [Transfer] {
        try await request("/transfers", token: token)
    }

    func createTransfer(token: String, recipient: String, filename: String,
                        content: String, programs: [String]) async throws -> Transfer {
        try await request("/transfers", method: "POST",
                          body: ["recipient": recipient, "filename": filename,
                                 "content": content, "programs": programs],
                          token: token)
    }

    func revokeTransfer(token: String, tid: String) async throws {
        struct Ok: Decodable {}
        let _: Ok = try await request("/transfers/\(tid)", method: "DELETE",
                                      token: token)
    }

    // MARK: Secure intake (request a file in; the sender submits with a token)

    func intakes(token: String) async throws -> [Intake] {
        try await request("/intakes", token: token)
    }

    func createIntake(token: String, fromParty: String, purpose: String?,
                      programs: [String]) async throws -> Intake {
        var body: [String: Any] = ["from_party": fromParty, "programs": programs]
        if let purpose, !purpose.isEmpty { body["purpose"] = purpose }
        return try await request("/intakes", method: "POST", body: body,
                                 token: token)
    }

    func intakeFile(token: String, iid: String) async throws -> IntakeFile {
        try await request("/intakes/\(iid)/file", token: token)
    }

    func closeIntake(token: String, iid: String) async throws {
        struct Ok: Decodable {}
        let _: Ok = try await request("/intakes/\(iid)", method: "DELETE",
                                      token: token)
    }

    // MARK: Social-platform connectors (tenant data sources)

    func connectors(token: String) async throws -> [SocialConn] {
        try await request("/connectors", token: token)
    }

    func createConnector(token: String, platform: String, direction: String,
                         handle: String?) async throws -> SocialConn {
        var body: [String: Any] = ["platform": platform, "direction": direction]
        if let handle, !handle.isEmpty { body["handle"] = handle }
        return try await request("/connectors", method: "POST", body: body,
                                 token: token)
    }

    func connectorIngest(token: String, cid: String, content: String) async throws {
        struct Ok: Decodable {}
        let _: Ok = try await request("/connectors/\(cid)/ingest", method: "POST",
                                      body: ["items": [["content": content]]],
                                      token: token)
    }

    func connectorScrape(token: String, cid: String) async throws {
        struct Ok: Decodable {}
        let _: Ok = try await request("/connectors/\(cid)/scrape", method: "POST",
                                      token: token)
    }

    func connectorPublish(token: String, cid: String, content: String) async throws {
        struct Ok: Decodable {}
        let _: Ok = try await request("/connectors/\(cid)/publish", method: "POST",
                                      body: ["content": content], token: token)
    }

    func revokeConnector(token: String, cid: String) async throws {
        struct Ok: Decodable {}
        let _: Ok = try await request("/connectors/\(cid)", method: "DELETE",
                                      token: token)
    }

    /// The sender's side: submit a file into an open intake. Authenticated by
    /// the one-shot submit token (X-Submit-Token), not the tenant bearer.
    func submitIntake(iid: String, submitToken: String, filename: String,
                      content: String) async throws {
        var req = URLRequest(url: base.appendingPathComponent("/intakes/\(iid)/submit"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "content-type")
        // The language the reader actually speaks. Every sentence the
        // backend composes on a public route is chosen from this header,
        // and no native shell was sending it — the browser sends it for
        // free, which is why the phones were the ones still answering in
        // English after the routes learned to speak.
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        req.setValue(submitToken, forHTTPHeaderField: "X-Submit-Token")
        req.httpBody = try JSONSerialization.data(withJSONObject: [
            "filename": filename, "content": content])
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse,
              (200..<300).contains(http.statusCode) else {
            // A 422 answers with a *list* of rows, not a string, so `as? String`
            // gave nil and the person saw the status code — less than they saw
            // before their language was ever considered. `message` is the
            // sentence the backend composes beside the rows; read it first.
            let body = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
            let said = (body?["message"] as? String) ?? (body?["detail"] as? String)
            throw ApiError.http(said ?? "submit failed")
        }
    }
}

/// What the deployment can and cannot reach.
///
/// Offline mode was settable and unreadable: the flag existed, the guarantee
/// was written in a docstring, and there was nowhere on a phone to see the
/// answer. A guarantee nobody can check is a guarantee.
struct OfflinePosture: Decodable {
    let offline: Bool
    let external_transmission_possible: Bool
    let local_destinations_allowed: String
    let guarantees: [String]
}
