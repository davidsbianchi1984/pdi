import Foundation

// MARK: - Wire models (mirror pdi/api.py)

struct KeysResponse: Decodable { let keys: [String] }
struct VaultRecord: Decodable { let key: String; let value: String; let updated_at: String? }
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

    private func request<T: Decodable>(_ path: String, method: String = "GET",
                                       body: [String: Any]? = nil, token: String) async throws -> T {
        var req = URLRequest(url: base.appendingPathComponent(path))
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "content-type")
        req.setValue("Bearer \(token)", forHTTPHeaderField: "authorization")
        if let body { req.httpBody = try JSONSerialization.data(withJSONObject: body) }

        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse else { throw ApiError.http("No response") }
        guard (200..<300).contains(http.statusCode) else {
            let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String
            throw ApiError.http(detail ?? "HTTP \(http.statusCode)")
        }
        if data.isEmpty { return try JSONDecoder().decode(T.self, from: Data("{}".utf8)) }
        return try JSONDecoder().decode(T.self, from: data)
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

    /// The sender's side: submit a file into an open intake. Authenticated by
    /// the one-shot submit token (X-Submit-Token), not the tenant bearer.
    func submitIntake(iid: String, submitToken: String, filename: String,
                      content: String) async throws {
        var req = URLRequest(url: base.appendingPathComponent("/intakes/\(iid)/submit"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "content-type")
        req.setValue(submitToken, forHTTPHeaderField: "X-Submit-Token")
        req.httpBody = try JSONSerialization.data(withJSONObject: [
            "filename": filename, "content": content])
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse,
              (200..<300).contains(http.statusCode) else {
            let detail = (try? JSONSerialization.jsonObject(with: data)
                          as? [String: Any])?["detail"] as? String
            throw ApiError.http(detail ?? "submit failed")
        }
    }
}
