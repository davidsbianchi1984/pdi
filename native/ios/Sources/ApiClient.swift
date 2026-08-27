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
struct AcceptanceCheck: Decodable, Identifiable {
    let check: String
    let says: String
    let passed: Bool
    let detail: String
    var id: String { check }
}

/// Appendix C, generated rather than typed: dated, pass/fail, per check.
struct AcceptanceReport: Decodable {
    let at: String
    let deployment: String
    let passing: Int
    let of: Int
    let clean: Bool
    let note: String
    let checks: [AcceptanceCheck]
}

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

struct IngestResult: Decodable { let sealed_at_rest: Bool; let key: String }
struct RobotData: Decodable { let keys: [String] }

struct ComplianceProgram: Decodable { let key: String; let label: String }
struct CompliancePrograms: Decodable { let programs: [ComplianceProgram] }

struct Transfer: Decodable {
    let id: String
    let recipient: String
    let filename: String
    let status: String
    let program_keys: [String]
    let retention_days: Int?
    let expires_at: String?
    let receive_token: String?     // present only on creation — shown once
}

struct Intake: Decodable {
    let id: String
    let from_party: String
    let purpose: String?
    let status: String
    let program_keys: [String]
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
    /// A rotation count, not a semantic version — `/health` uses `version`
    /// for the latter and the two cannot share a wire name.
    let generation: Int
    let active: Bool
    let created_at: String?
    var id: Int { generation }
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
        // One trailing slash was removed where the other three clients
        // remove them all, so `http://host//` survived only here.
        let t = String(s.reversed().drop(while: { $0 == "/" }).reversed())
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

    // -- the resident intelligence (pdi/resident.py) ------------------------
    // The agent living in the vault process: planner, closed tool registry,
    // queryable datasets, embeddings, local-only inference. One engine for a
    // facility tenant and a standard HTTPS tenant alike.

    func residentPosture(token: String) async throws -> ResidentPosture {
        try await request("/resident", token: token)
    }

    func residentPlan(goal: String, everyHours: Double? = nil,
                      token: String) async throws -> ResidentTask {
        var body: [String: Any] = ["goal": goal]
        // A standing task: the vault re-runs the plan on this interval.
        if let everyHours { body["every_hours"] = everyHours }
        return try await request("/resident/tasks", method: "POST",
                                 body: body, token: token)
    }

    struct ResidentCancelled: Decodable {
        let id: String
        let cancelled: Bool
    }

    /// The off switch: end a task's future; the record of its runs stays.
    func residentCancel(tid: String, token: String) async throws
        -> ResidentCancelled {
        try await request("/resident/tasks/\(tid)", method: "DELETE",
                          token: token)
    }

    func residentTasks(token: String) async throws -> [ResidentTask] {
        try await request("/resident/tasks", token: token)
    }

    func residentRun(tid: String, token: String) async throws -> ResidentTask {
        try await request("/resident/tasks/\(tid)/run", method: "POST",
                          token: token)
    }

    struct ResidentRunRow: Decodable {
        let id: String
        let ran_at: String
        let status: String
        let note: String?
    }

    /// The task's past cycles, newest first — a standing task's step rows
    /// reset each cycle, so the ledger is the only history there is.
    func residentRuns(tid: String, token: String) async throws
        -> [ResidentRunRow] {
        try await request("/resident/tasks/\(tid)/runs", token: token)
    }

    func residentDatasets(token: String) async throws -> [ResidentDataset] {
        try await request("/resident/datasets", token: token)
    }

    /// Rows are whatever columns the plan wrote, so they are shown as the
    /// JSON they are rather than decoded into a shape this shell invents.
    func residentRows(name: String, token: String) async throws -> [String] {
        var req = URLRequest(url: base.appendingPathComponent(
            "/resident/datasets/\(name)/rows"))
        req.setValue("Bearer \(token)", forHTTPHeaderField: "authorization")
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        let (data, _) = try await URLSession.shared.data(for: req)
        guard let body = try JSONSerialization.jsonObject(with: data)
                as? [String: Any],
              let rows = body["dataset_rows"] as? [[String: Any]] else { return [] }
        return rows.map { row in
            (try? JSONSerialization.data(withJSONObject: row,
                                         options: [.sortedKeys]))
                .flatMap { String(data: $0, encoding: .utf8) } ?? ""
        }
    }

    func residentEmbed(key: String, text: String,
                       token: String) async throws -> ResidentEmbedOut {
        try await request("/resident/embeddings", method: "POST",
                          body: ["key": key, "text": text], token: token)
    }

    func residentForget(key: String, token: String) async throws -> Int {
        struct ForgetOut: Decodable { let vectors_removed: Int }
        let out: ForgetOut = try await request(
            "/resident/embeddings/\(key)", method: "DELETE", token: token)
        return out.vectors_removed
    }

    func residentSearch(query: String,
                        token: String) async throws -> ResidentSearchOut {
        try await request("/resident/search", method: "POST",
                          body: ["query": query], token: token)
    }

    struct ResidentSpoken: Decodable {
        let model: String
        let text: String
        let leaves_host: Bool
    }

    /// One local turn from the vault's own model — the prompt never
    /// leaves the host, and the answer names which engine spoke.
    func residentInfer(prompt: String,
                       token: String) async throws -> ResidentSpoken {
        try await request("/resident/infer", method: "POST",
                          body: ["prompt": prompt], token: token)
    }

    struct ResidentAnswer: Decodable {
        let model: String
        let text: String
        let leaves_host: Bool
        let drew_on: [String]
    }

    /// Grounded: the question ranks this tenant's vectors, the matched
    /// seals are read back, and the local model answers from them.
    func residentAsk(question: String,
                     token: String) async throws -> ResidentAnswer {
        try await request("/resident/ask", method: "POST",
                          body: ["question": question], token: token)
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

    /// Section 10's five acceptance criteria, run against this deployment.
    ///
    /// Client-run by design: a guarantee only the vendor can demonstrate is a
    /// vendor assurance, and that is the thing a sovereignty proposition is
    /// explicitly not selling.
    func acceptance(token: String) async throws -> AcceptanceReport {
        try await request("/acceptance", token: token)
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

    // MARK: the key itself — whose hands it is in

    func tenantKey(token: String) async throws -> TenantKeyOut {
        try await request("/key", token: token)
    }

    func setTenantKey(provider: String, key: String?,
                      token: String) async throws -> TenantKeyOut {
        var body: [String: Any] = ["provider": provider]
        if let key, !key.isEmpty { body["key"] = key }
        return try await request("/key", method: "PUT", body: body,
                                 token: token)
    }

    /// Hands the tenant back to deployment custody. A 409 if it never left,
    /// which the operator needs told rather than shown as a failure.
    func surrenderTenantKey(token: String) async throws -> TenantKeyOut {
        try await request("/key", method: "DELETE", token: token)
    }

    func resealUnderNewKey(adminToken: String) async throws -> ResealOut {
        try await request("/keys/reseal", method: "POST", token: adminToken)
    }

    func revokeToken(_ minted: String, adminToken: String) async throws -> Ok {
        try await request("/tokens/\(minted)", method: "DELETE",
                          token: adminToken)
    }

    // MARK: connectors — the catalog, and each connection's own code

    /// Parsed by hand: the catalog is a map of platforms, and the door is
    /// the fetch.
    func connectorCatalog() async throws -> Int {
        var req = URLRequest(url: base.appendingPathComponent("/connectors/catalog"))
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        let (data, _) = try await URLSession.shared.data(for: req)
        let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
        for value in obj?.values ?? [String: Any]().values {
            if let list = value as? [Any] { return list.count }
            if let map = value as? [String: Any] { return map.count }
        }
        return obj?.count ?? 0
    }

    func connectorBeacon(cid: String, token: String) async throws -> Data {
        var req = URLRequest(url: base.appendingPathComponent(
            "/connectors/\(cid)/beacon"))
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        req.setValue("Bearer \(token)", forHTTPHeaderField: "authorization")
        let (data, _) = try await URLSession.shared.data(for: req)
        return data
    }

    func connectorQrUrl(cid: String) -> URL {
        base.appendingPathComponent("/connectors/\(cid)/qr.svg")
    }

    func unbindRobot(rid: String, token: String) async throws -> Ok {
        try await request("/robots/\(rid)", method: "DELETE", token: token)
    }

    // MARK: the guide, the pane in the corner, and the translator

    func guideOutline() async throws -> GuideOutlineOut {
        try await request("/console/guide")
    }

    func guideStep(key: String) async throws -> GuideStepOut {
        try await request("/console/guide/steps/\(key)")
    }

    func guideForScreen(number: Int) async throws -> GuideStepOut {
        try await request("/console/guide/for-screen/\(number)")
    }

    func guideStart(learner: String) async throws -> GuideWhereOut {
        try await request("/console/guide/start", method: "POST",
                          body: ["learner_id": learner])
    }

    func guideProgress(learner: String) async throws -> GuideWhereOut {
        try await request("/console/guide/progress/\(learner)")
    }

    func guideDone(learner: String, lesson: String) async throws -> GuideWhereOut {
        try await request("/console/guide/done", method: "POST",
                          body: ["learner_id": learner, "lesson": lesson])
    }

    func consoleAsk(question: String) async throws -> AskOut {
        try await request("/console/ask", method: "POST",
                          body: ["question": question])
    }

    /// Dictionary-only on the backend: PDI runs no model, so it translates
    /// exactly its own note strings and the engine field says which happened.
    func translate(text: String, token: String) async throws -> TranslateOut {
        try await request("/translate", method: "POST", body: ["text": text],
                          token: token)
    }

    func dockVocabulary() async throws -> DockVocabOut {
        try await request("/dock/faces")
    }

    func dockWhere(face: String) async throws -> DockWhereOut {
        try await request("/dock/where/\(face)")
    }

    func dockSettings(tid: String, token: String) async throws -> DockSettingsOut {
        try await request("/dock/\(tid)", token: token)
    }

    func dockConfigure(tid: String, corner: String,
                       token: String) async throws -> DockSettingsOut {
        try await request("/dock/\(tid)", method: "PUT",
                          body: ["corner": corner], token: token)
    }

    func dockFace(tid: String, name: String,
                  token: String) async throws -> DockFaceOut {
        try await request("/dock/\(tid)/face/\(name)", token: token)
    }

    // MARK: exchange details — one transfer, one intake, and their chains

    func transferOne(tid: String, token: String) async throws -> Transfer {
        try await request("/transfers/\(tid)", token: token)
    }

    func transferCustody(tid: String, token: String) async throws -> CustodyChainOut {
        try await request("/transfers/\(tid)/custody", token: token)
    }

    /// The recipient's act. Not the tenant's token — the one-shot receive
    /// token is the whole credential, riding as its own header the way the
    /// intake submit already does.
    func receiveTransfer(tid: String,
                         receiveToken: String) async throws -> ReceivedFileOut {
        var req = URLRequest(url: base.appendingPathComponent(
            "/transfers/\(tid)/receive"))
        req.httpMethod = "POST"
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        req.setValue(receiveToken, forHTTPHeaderField: "x-receive-token")
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse,
              (200..<300).contains(http.statusCode) else {
            throw ApiError.http("the receive token did not open it")
        }
        return try JSONDecoder().decode(ReceivedFileOut.self, from: data)
    }

    func intakeOne(iid: String, token: String) async throws -> Intake {
        try await request("/intakes/\(iid)", token: token)
    }

    func intakeCustody(iid: String, token: String) async throws -> CustodyChainOut {
        try await request("/intakes/\(iid)/custody", token: token)
    }

    // MARK: positions — the assistant builder

    func buildPosition(industry: String, jobTitle: String,
                       token: String) async throws -> BlueprintOut {
        try await request("/positions", method: "POST",
                          body: ["industry": industry,
                                 "role": ["job_title": jobTitle]],
                          token: token)
    }

    func listPositions(token: String) async throws -> PositionsListOut {
        try await request("/positions", token: token)
    }

    func getPosition(id: String, token: String) async throws -> BlueprintOut {
        try await request("/positions/\(id)", token: token)
    }

    // MARK: posture — where the vault lives, and whether it is up

    func health() async throws -> HealthOut {
        try await request("/health")
    }

    /// Parsed by hand rather than declared: the reply is a map keyed by
    /// mode id, and a record nested under an arbitrary-key map is a shape
    /// the wire guard rightly refuses to vouch for.
    func hostingModes() async throws -> [(id: String, label: String)] {
        var req = URLRequest(url: base.appendingPathComponent("/hosting"))
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        let (data, _) = try await URLSession.shared.data(for: req)
        let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
        let modes = obj?["modes"] as? [String: [String: Any]] ?? [:]
        return modes.map { entry in
            let title = (entry.value["title"] as? String) ?? entry.key
            let price = (entry.value["price"] as? String) ?? ""
            return (id: entry.key, label: "\(title) · \(price)")
        }.sorted { $0.id < $1.id }
    }

    func hosting(tid: String, token: String) async throws -> HostingModeOut {
        try await request("/hosting/\(tid)", token: token)
    }

    func hostingHistory(tid: String, token: String) async throws -> HostingHistoryOut {
        try await request("/hosting/\(tid)/history", token: token)
    }

    func setHosting(tid: String, mode: String,
                    token: String) async throws -> Ok {
        try await request("/hosting/\(tid)", method: "PUT",
                          body: ["mode": mode], token: token)
    }

    func recordDeployment(token: String) async throws -> Ok {
        try await request("/deployments", method: "POST",
                          body: ["name": "new site", "option": "colocation"],
                          token: token)
    }

    func operations(token: String) async throws -> OperationsOut {
        try await request("/operations", token: token)
    }

    func auditSchema() async throws -> AuditSchemaOut {
        try await request("/audit/schema")
    }

    /// The tenant's own standing, which is a smaller shape than the
    /// operator's BAA record: executed, since when, and the refusal note
    /// when nothing is on file. Names live on the admin route only.
    func baaStatus(token: String) async throws -> BaaStandingOut {
        try await request("/baa", token: token)
    }

    // MARK: continuity — bequests, and what outlives the tenant

    func bequests(token: String) async throws -> [BequestOut] {
        try await request("/bequests", token: token)
    }

    func createBequest(grantee: String, prefixes: [String], note: String?,
                       token: String) async throws -> BequestOut {
        var body: [String: Any] = ["grantee_name": grantee,
                                   "key_prefixes": prefixes]
        if let note, !note.isEmpty { body["note"] = note }
        return try await request("/bequests", method: "POST", body: body,
                                 token: token)
    }

    func revokeBequest(bid: String, token: String) async throws -> BequestOut {
        try await request("/bequests/\(bid)", method: "DELETE", token: token)
    }

    /// The executor's act: activation attests the condition — the reference
    /// goes into the audit chain — and mints the grant token, shown once.
    func activateBequest(bid: String, ref: String,
                         adminToken: String) async throws -> BequestOut {
        try await request("/bequests/\(bid)/activate", method: "POST",
                          body: ["activation_ref": ref], token: adminToken)
    }

    func revokeBequestGrant(bid: String,
                            adminToken: String) async throws -> RevokedOut {
        try await request("/bequests/\(bid)/grant", method: "DELETE",
                          token: adminToken)
    }

    /// The heir's side. Two separate secrets on purpose: the grant token
    /// says the condition was attested, the customer key decrypts. Holding
    /// one without the other opens nothing — so both ride as headers here,
    /// inline the way the intake submit already is.
    func bequestKeys(grantToken: String,
                     customerKey: String) async throws -> KeysListOut {
        var req = URLRequest(url: base.appendingPathComponent("/bequests/grant/keys"))
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        req.setValue(grantToken, forHTTPHeaderField: "x-grant-token")
        req.setValue(customerKey, forHTTPHeaderField: "x-tenant-key")
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse,
              (200..<300).contains(http.statusCode) else {
            throw ApiError.http("the grant did not open")
        }
        return try JSONDecoder().decode(KeysListOut.self, from: data)
    }

    func bequestRead(key: String, grantToken: String,
                     customerKey: String) async throws -> Data {
        var req = URLRequest(url: base.appendingPathComponent(
            "/bequests/grant/read?key=\(key)"))
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        req.setValue(grantToken, forHTTPHeaderField: "x-grant-token")
        req.setValue(customerKey, forHTTPHeaderField: "x-tenant-key")
        let (data, _) = try await URLSession.shared.data(for: req)
        return data
    }

    // MARK: contributions, the snapshot, and the custody ops

    func contributions(token: String) async throws -> ContribCount {
        try await request("/contributions", token: token)
    }

    func contribute(source: String, ref: String?,
                    token: String) async throws -> ContribOut {
        var body: [String: Any] = ["source": source, "kind": "outcome",
                                   "payload": ["helped": true]]
        if let ref, !ref.isEmpty { body["ref"] = ref }
        return try await request("/contributions", method: "POST",
                                 body: body, token: token)
    }

    func withdrawContribution(ref: String, token: String) async throws -> Ok {
        try await request("/contributions/\(ref)", method: "DELETE",
                          token: token)
    }

    /// The whole tenant, in hand — raw on purpose: records are arbitrary
    /// JSON and the door is the fetch, not a schema. Held so a restore can
    /// put back exactly what was taken.
    private var lastSnapshot: [[String: Any]] = []

    func snapshotRecords(token: String) async throws -> Int {
        var req = URLRequest(url: base.appendingPathComponent("/snapshot"))
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        req.setValue("Bearer \(token)", forHTTPHeaderField: "authorization")
        let (data, _) = try await URLSession.shared.data(for: req)
        let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        lastSnapshot = obj?["records"] as? [[String: Any]] ?? []
        return lastSnapshot.count
    }

    func restoreSnapshot(token: String) async throws -> Ok {
        try await request("/restore", method: "POST",
                          body: ["records": lastSnapshot], token: token)
    }

    func retentionPolicy(adminToken: String) async throws -> RetentionPolicyOut {
        try await request("/retention", token: adminToken)
    }

    func retentionSweep(adminToken: String) async throws -> SweepOut {
        try await request("/retention/sweep", method: "POST",
                          token: adminToken)
    }

    func seedDemo(adminToken: String) async throws -> Ok {
        try await request("/seed", method: "POST", token: adminToken)
    }

    // MARK: tenants — the operator's half

    func createTenant(name: String, adminToken: String) async throws -> TenantMade {
        try await request("/tenants", method: "POST",
                          body: ["name": name], token: adminToken)
    }

    func restoreTenant(tid: String, adminToken: String) async throws -> Ok {
        try await request("/tenants/\(tid)/restore", method: "POST",
                          token: adminToken)
    }

    /// `mode` decides whether the tenant can come back. The audit trail
    /// survives either way — that is the point of a hash chain.
    func deleteTenant(tid: String, mode: String,
                      adminToken: String) async throws -> Ok {
        try await request("/tenants/\(tid)?mode=\(mode)", method: "DELETE",
                          token: adminToken)
    }

    func mintTenantToken(tid: String, role: String,
                         adminToken: String) async throws -> MintedToken {
        try await request("/tenants/\(tid)/tokens", method: "POST",
                          body: ["role": role], token: adminToken)
    }

    func setTenantRetention(tid: String, retention: String,
                            adminToken: String) async throws -> RetentionSet {
        try await request("/tenants/\(tid)/retention", method: "PUT",
                          body: ["retention": retention], token: adminToken)
    }

    func tenantBaa(tid: String, adminToken: String) async throws -> BaaOut {
        try await request("/tenants/\(tid)/baa", token: adminToken)
    }

    func recordTenantBaa(tid: String, customer: String, operatorName: String,
                         date: String, adminToken: String) async throws -> BaaOut {
        try await request("/tenants/\(tid)/baa", method: "POST",
                          body: ["customer_legal_name": customer,
                                 "operator_legal_name": operatorName,
                                 "effective_date": date], token: adminToken)
    }

    func rescindTenantBaa(tid: String, adminToken: String) async throws -> Ok {
        try await request("/tenants/\(tid)/baa", method: "DELETE",
                          token: adminToken)
    }

    // MARK: the agent at the gate — what it may do, who is on shift

    func gateCeiling(token: String) async throws -> GateCeilingOut {
        try await request("/gate/ceiling", token: token)
    }

    func gateChannel(token: String) async throws -> GateChannelOut {
        try await request("/gate/channel", token: token)
    }

    func gateRoster(token: String) async throws -> GateRosterOut {
        try await request("/gate/roster", token: token)
    }

    func addToRoster(name: String, role: String,
                     token: String) async throws -> RosterEntryOut {
        try await request("/gate/roster", method: "POST",
                          body: ["name": name, "role": role], token: token)
    }

    func removeFromRoster(rid: String, token: String) async throws -> RemovedOut {
        try await request("/gate/roster/\(rid)", method: "DELETE", token: token)
    }

    func setGateTimezone(_ timezone: String, token: String) async throws -> TzOut {
        try await request("/gate/timezone", method: "PUT",
                          body: ["timezone": timezone], token: token)
    }

    func gatePages(token: String) async throws -> [GatePageOut] {
        try await request("/gate/pages", token: token)
    }

    func retryGatePage(pid: String, token: String) async throws -> GatePageOut {
        try await request("/gate/pages/\(pid)/retry", method: "POST",
                          token: token)
    }

    // MARK: carriers — custody codes on sealed things

    func carrierBeacons(token: String) async throws -> [CarrierBeacon] {
        try await request("/beacons", token: token)
    }

    func placeCarrierBeacon(label: String, refKind: String, disclose: String,
                            token: String) async throws -> CarrierBeacon {
        try await request("/beacons", method: "POST",
                          body: ["ref_kind": refKind, "label": label,
                                 "disclose": disclose], token: token)
    }

    func carrierBeacon(bid: String, token: String) async throws -> CarrierBeacon {
        try await request("/beacons/\(bid)", token: token)
    }

    func setCarrierState(bid: String, state: String,
                         token: String) async throws -> CarrierBeacon {
        try await request("/beacons/\(bid)/state", method: "PUT",
                          body: ["state": state], token: token)
    }

    func liftCarrierBeacon(bid: String, token: String) async throws -> Lifted {
        try await request("/beacons/\(bid)", method: "DELETE", token: token)
    }

    func carrierCustody(bid: String, token: String) async throws -> CustodyChainOut {
        try await request("/beacons/\(bid)/custody", token: token)
    }

    /// The scanner's half — no bearer at all: the code in the hand is the
    /// whole credential, and what it earns is capped by `disclose`.
    func scanCard(bid: String) async throws -> ScanCardOut {
        try await request("/s/\(bid)/card")
    }

    /// The landing page and its QR image. The JSON helper cannot carry
    /// either, so the door is the URL the opener fetches; building it here
    /// is what the route audit reads, and GET stands absent a verb.
    func scanPageUrl(bid: String) -> URL {
        base.appendingPathComponent("/s/\(bid)")
    }

    func scanQrUrl(bid: String) -> URL {
        base.appendingPathComponent("/s/\(bid)/qr.svg")
    }

    func reportFound(bid: String) async throws -> FoundAck {
        try await request("/s/\(bid)/found", method: "POST",
                          body: ["where": "loading dock"])
    }

    func ringHolder(bid: String) async throws -> RingRow {
        try await request("/s/\(bid)/ring", method: "POST",
                          body: ["kind": "delivery"])
    }

    func rings(token: String) async throws -> [RingRow] {
        try await request("/rings", token: token)
    }

    func ringTranscript(rid: String, token: String) async throws -> RingRow {
        try await request("/rings/\(rid)/transcript", token: token)
    }

    /// Resolve the recipient's page before the link goes into an email — a
    /// misconfigured public base would otherwise be discovered by the
    /// recipient, who has nobody to ask.
    func checkRecipientPage(tid: String) async throws -> Bool {
        var req = URLRequest(url: base.appendingPathComponent("/r/\(tid)"))
        req.setValue(L10n.deviceLanguage, forHTTPHeaderField: "accept-language")
        let (_, resp) = try await URLSession.shared.data(for: req)
        return ((resp as? HTTPURLResponse)?.statusCode ?? 0) < 400
    }

    /// How to open this console on a phone: same Wi-Fi, no app store.
    func pairInfo() async throws -> PairInfoOut {
        try await request("/pair")
    }

    func pairQrUrl() -> URL {
        base.appendingPathComponent("/pair/qr.svg")
    }
}

/// `version` is optional twice over: a backend old enough to predate the
/// field answers without it, and that case is exactly the one the version
/// guard exists to catch — so decoding must survive its absence rather than
/// throw and leave the shell with no answer at all. It was decoded away
/// entirely until the guard needed it; a binding that discards the answer is
/// worse than none, because the next person to want it finds a health call
/// that looks complete.
struct HealthOut: Decodable { let status: String; let version: String? }

struct GuideOutlineOut: Decodable { let steps: Int }

struct GuideStepOut: Decodable {
    let key: String
    let title: String
    let what: String?
    let speak: String?
}

struct GuideWhereOut: Decodable {
    let step: GuideStepOut?
    let done: Int
    let total: Int
    let note: String
}

struct AskOut: Decodable {
    let answer: String
    let refused: Bool
}

struct TranslateOut: Decodable {
    let translation: String
    let engine: String
}

struct DockVocabOut: Decodable {
    let default_face: String
    let default_state: String
}

struct DockWhereOut: Decodable {
    let title: String
    let path: String
}

struct DockSettingsOut: Decodable {
    let corner: String
    let state: String
    let face: String
}

struct DockFaceOut: Decodable { let shows: String }

struct TenantKeyOut: Decodable {
    let provider: String
    let customer_managed: Bool
    let operator_can_decrypt: Bool
    let note: String
}

struct ResealOut: Decodable {
    let active_version: Int
    let resealed: Int
    let customer_managed_skipped: Int
}

struct ReceivedFileOut: Decodable {
    let filename: String?
    let content: String?
}

struct BlueprintOut: Decodable { let id: String; let industry: String }
struct PositionsListOut: Decodable { let count: Int; let ids: [String] }

struct BaaStandingOut: Decodable {
    let executed: Bool
    let effective_date: String?
    let note: String?
}

struct HostingModeOut: Decodable {
    let title: String
    let price: String
    let means: String
    let free_because: String?
    let we_are_responsible_for: [String]
    let you_are_responsible_for: [String]
    let mode: String?
}

struct HistoryRow: Decodable { let mode: String?; let at: String? }
struct HostingHistoryOut: Decodable { let history: [HistoryRow] }

struct OperationsEntryOut: Decodable { let key: String; let updated_at: String }
struct OperationsOut: Decodable {
    let entries: [OperationsEntryOut]
    let note: String
}

struct AuditSchemaOut: Decodable {
    let actions: [AuditActionOut]
    let retention: String
}
struct AuditActionOut: Decodable { let action: String; let category: String }

struct BequestOut: Decodable {
    let id: String
    let grantee_name: String
    let condition: String?
    let key_prefixes: [String]
    let note: String?
    let activated: Bool
    let revoked: Bool
    let activation_ref: String?
    let grant_token: String?
}

struct RevokedOut: Decodable { let revoked: Bool }
struct KeysListOut: Decodable { let keys: [String] }
struct ContribCount: Decodable { let count: Int; let keys: [String] }

struct ContribOut: Decodable {
    let id: String
    let key: String
    let sealed_at_rest: Bool
}

struct RetentionPolicyOut: Decodable {
    let recovery_window: String
    let windows: [String]
}

struct SweepOut: Decodable {
    let purged_tenants: Int
    let expired_records: Int
    let recovery_window: String
}

struct TenantMade: Decodable { let id: String; let name: String; let token: String }
struct MintedToken: Decodable { let token: String }
struct RetentionSet: Decodable { let retention: String }

struct BaaOut: Decodable {
    let executed: Bool
    let effective_date: String?
    let customer_legal_name: String?
    let operator_legal_name: String?
    let note: String?
}

struct GateCeilingOut: Decodable {
    let rule: String
    let may: [String: String]
    let may_never: [String: String]
}

struct GateChannelOut: Decodable {
    let configured: Bool
    let signed: Bool?
    let note: String?
}

struct RosterEntryOut: Decodable { let id: String; let name: String; let role: String }

struct GateRosterOut: Decodable {
    let configured: Bool
    let roster: [RosterEntryOut]
    let anybody_on_shift: Bool
    let timezone: String?
}

struct RemovedOut: Decodable { let removed: Bool }
struct TzOut: Decodable { let tenant_id: String; let timezone: String }

struct GatePageOut: Decodable {
    let id: String?
    let state: String?
}

/// A custody code on a sealed thing. `disclose` is a single value: `blind`
/// proves custody and says nothing else; `contact` adds a way to reach
/// whoever holds it.
struct CarrierBeacon: Decodable {
    let id: String
    let ref_kind: String
    let label: String
    let disclose: String
    let state: String
    let scans: Int
    let active: Bool
}

struct Lifted: Decodable { let id: String; let active: Bool }

/// What a scanner sees. `contents` is always null on the wire and that is
/// the feature: the code proves custody, it does not open the thing.
struct ScanCardOut: Decodable {
    let reference: String
    let kind: String
    let state: String
    let under_custody: Bool
    let badge: String
    let note: String
    let held_by: String?
}

struct CustodyEntryOut: Decodable {
    let event: String
    let actor: String
    let at: String
}

struct CustodyChainOut: Decodable {
    let chain_of_custody: [CustodyEntryOut]
    let audit_chain_intact: Bool
}

struct FoundAck: Decodable {
    let beacon: String
    let recorded: Bool
    let note: String
}

struct RingRow: Decodable {
    let id: String
    let kind: String?
    let note: String?
    let state: String?
    let outcome: String?
    let created_at: String?
}

struct PairInfoOut: Decodable {
    let console_url: String
    let how: [String]
    let note: String
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

// The resident intelligence's wire shapes (pdi/resident.py). `leaves_host`
// travels with every tool and step on purpose: a person deciding whether to
// run a plan should not have to read Python to learn which steps go outside.
struct ResidentTool: Decodable {
    let name: String
    let means: String
    let leaves_host: Bool
}
struct ResidentPosture: Decodable {
    let resident: Bool
    let means: String
    let hosting_mode: String
    let in_facility: Bool
    let local_model: String?
    let embedder: String
    let tools: [ResidentTool]
    let privacy: String
}
struct ResidentStepOut: Decodable {
    let position: Int
    let title: String
    let tool: String
    let leaves_host: Bool
    let status: String
    let result_ref: String?
    let summary: String?
    let error: String?
}
struct ResidentTask: Decodable {
    let id: String
    let goal: String
    let status: String
    let planned_by: String
    let plan_steps: [ResidentStepOut]
    // Standing tasks: the vault re-runs the plan on this interval itself.
    let every_hours: Double?
    let next_run_at: String?
}
struct ResidentDataset: Decodable {
    let dataset: String
    let row_count: Int
    let last_write: String
}
struct ResidentEmbedOut: Decodable {
    let key: String
    let embedder: String
    let dim: Int
}
struct ResidentMatch: Decodable { let key: String; let score: Double }
struct ResidentSearchOut: Decodable {
    let query: String
    let matches: [ResidentMatch]
}
