import SwiftUI

/// Dashboard: record count + audit integrity, pulled from the live vault.
struct OverviewView: View {
    @EnvironmentObject var state: AppState
    @State private var count: Int?
    @State private var intact: Bool?
    @State private var loading = true

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                HStack(spacing: 8) {
                    Circle().fill(Theme.green).frame(width: 8, height: 8)
                    Text("Vault unlocked").font(.caption.bold()).foregroundStyle(Theme.green)
                }
                Text("Your vault").font(.title.bold()).foregroundStyle(Theme.txt)
                Text("Records are sealed at rest; every access is written to a tamper-evident audit chain.")
                    .font(.subheadline).foregroundStyle(Theme.t2)

                HStack(spacing: 12) {
                    stat("Records", loading ? "—" : "\(count ?? 0)", Theme.brandA)
                    stat("Audit", loading ? "—" : (intact == true ? "Intact" : "Broken"),
                         intact == false ? Theme.red : Theme.green)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Token").font(.headline).foregroundStyle(Theme.txt)
                    Text(masked(state.token ?? "")).font(.system(.subheadline, design: .monospaced))
                        .foregroundStyle(Theme.t2)
                    Text(state.baseURL).font(.caption).foregroundStyle(Theme.t3)
                }.card()

                Button("Sign out") { state.signOut() }
                    .font(.subheadline).foregroundStyle(Theme.t2)
                    .frame(maxWidth: .infinity).padding(.vertical, 12)
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(Theme.line, lineWidth: 1))
            }.padding(20)
        }
        .task { await load() }
    }

    private func stat(_ label: String, _ value: String, _ tint: Color) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(value).font(.title2.bold()).foregroundStyle(tint)
            Text(label).font(.caption).foregroundStyle(Theme.t2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .card()
    }

    private func masked(_ t: String) -> String {
        guard t.count > 8 else { return "••••" }
        return t.prefix(6) + "…" + t.suffix(4)
    }

    private func load() async {
        guard let token = state.token else { return }
        loading = true
        count = (try? await ApiClient.shared.keys(token: token))?.count
        intact = (try? await ApiClient.shared.auditVerify(token: token))?.intact
        loading = false
    }
}
