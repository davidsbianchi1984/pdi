import SwiftUI

/// Holds the tenant bearer token + base URL, persisted to UserDefaults so the
/// app resumes signed-in. Drives the root switch between Sign-in and the tabs.
@MainActor
final class AppState: ObservableObject {
    @Published var token: String?
    @Published var baseURL: String = "http://127.0.0.1:8000"

    private let d = UserDefaults.standard

    init() {
        token = d.string(forKey: "pdi.token")
        baseURL = d.string(forKey: "pdi.base") ?? "http://127.0.0.1:8000"
    }

    var isSignedIn: Bool { token != nil }

    func signIn(token: String, base: String) {
        self.token = token
        self.baseURL = base
        d.set(token, forKey: "pdi.token")
        d.set(base, forKey: "pdi.base")
    }

    func signOut() {
        token = nil
        ["pdi.token"].forEach { d.removeObject(forKey: $0) }
    }
}
