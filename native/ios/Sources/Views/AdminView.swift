import SwiftUI

/// Admin: key management. Gated by the deployment's PDI_ADMIN_TOKEN — a
/// different credential from the tenant token, pasted here and kept only in
/// memory. Rotation re-seals every record immediately; retire deletes
/// non-active versions (safe only after a reseal).
struct AdminCard: View {
    @EnvironmentObject var state: AppState
    @State private var adminToken = ""
    @State private var info: KeysInfo?
    @State private var status: String?
    @State private var error: String?
    @State private var held: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Admin · Key management").font(.headline).foregroundStyle(Theme.txt)
            Text("Requires the deployment's admin token (PDI_ADMIN_TOKEN) — not the tenant token. Kept in memory only, never stored.")
                .font(.caption).foregroundStyle(Theme.t2)
            SecureField("admin token", text: $adminToken)
                .foregroundStyle(Theme.txt)
                .padding(10).background(Theme.scrBot)
                .clipShape(RoundedRectangle(cornerRadius: 11))
                .overlay(RoundedRectangle(cornerRadius: 11).stroke(Theme.line, lineWidth: 1))

            HStack(spacing: 8) {
                Button("Load versions") { load() }
                    .font(.caption.bold()).foregroundStyle(.white)
                    .padding(.horizontal, 12).padding(.vertical, 8)
                    .background(Theme.brandA).clipShape(Capsule())
                Button("Rotate key") { rotate() }
                    .font(.caption.bold()).foregroundStyle(.white)
                    .padding(.horizontal, 12).padding(.vertical, 8)
                    .background(Theme.amber).clipShape(Capsule())
                    .disabled(info == nil)
                Button("Retire old") { retire() }
                    .font(.caption.bold()).foregroundStyle(Theme.red)
                    .disabled(info == nil)
            }

            Button("What do you hold about us") { exportAll() }
                .font(.caption.bold()).foregroundStyle(.white)
                .padding(.horizontal, 12).padding(.vertical, 8)
                .background(Theme.brand).clipShape(Capsule())

            if let held {
                Text(held).font(.caption).foregroundStyle(Theme.t2)
            }

            if let info {
                Text("provider: \(info.provider)")
                    .font(.caption2).foregroundStyle(Theme.t3)
                ForEach(info.versions) { v in
                    HStack {
                        Circle().fill(v.active ? Theme.green : Theme.t3)
                            .frame(width: 8, height: 8)
                        Text("v\(v.version)").font(.caption.bold())
                            .foregroundStyle(Theme.txt)
                        Text(v.active ? "active" : "inactive")
                            .font(.caption2)
                            .foregroundStyle(v.active ? Theme.green : Theme.t3)
                        Spacer()
                        Text(v.created_at ?? "").font(.caption2).foregroundStyle(Theme.t3)
                    }
                }
            }
            if let status { Text(status).font(.caption).foregroundStyle(Theme.green) }
            if let error { Text(error).font(.caption).foregroundStyle(Theme.red) }
        }.card()
    }

    private func load() {
        error = nil; status = nil
        Task {
            do { info = try await ApiClient.shared.adminKeys(adminToken: adminToken) }
            catch { self.error = error.localizedDescription }
        }
    }

    private func rotate() {
        error = nil; status = nil
        Task {
            do {
                info = try await ApiClient.shared.rotateKey(adminToken: adminToken)
                status = "Rotated — every record re-sealed under the new version."
            } catch { self.error = error.localizedDescription }
        }
    }

    private func retire() {
        error = nil; status = nil
        Task {
            do {
                let r = try await ApiClient.shared.retireKeys(adminToken: adminToken)
                info = KeysInfo(provider: info?.provider ?? "env", versions: r.versions)
                status = "Retired \(r.retired) old version(s)."
            } catch { self.error = error.localizedDescription }
        }
    }
}

extension AdminCard {
    /// The portability door. Counts and table names on the phone; the
    /// document itself is what the console downloads.
    func exportAll() {
        Task {
            do {
                let all = try await ApiClient.shared.exportEverything(
                    token: state.token ?? "")
                let rows = all.tables.values.reduce(0) { $0 + $1.count }
                held = "\(all.tables.count) table(s), \(rows) row(s) — \(all.note)"
            } catch {
                self.error = error.localizedDescription
            }
        }
    }
}
