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
}
