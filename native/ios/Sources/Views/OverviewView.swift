import SwiftUI

/// Dashboard: record count + audit integrity, pulled from the live vault.
struct OverviewView: View {
    @EnvironmentObject var state: AppState
    @State private var count: Int?
    @State private var intact: Bool?
    @State private var loading = true
    @State private var languages: [LanguageInfo] = []
    @State private var language = "en"

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

                VStack(alignment: .leading, spacing: 8) {
                    Text("Language").font(.headline).foregroundStyle(Theme.txt)
                    Text("PDI's explanatory notes arrive in this language; sealed data is untouched.")
                        .font(.caption).foregroundStyle(Theme.t2)
                    Picker("", selection: $language) {
                        ForEach(languages, id: \.code) { l in
                            Text(l.label + (l.notes_translated == true
                                            ? "" : " (notes in English)")).tag(l.code)
                        }
                    }
                    .pickerStyle(.menu).tint(Theme.brandA)
                    .onChange(of: language) { _ in applyLanguage() }
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

    private func applyLanguage() {
        guard let token = state.token else { return }
        Task { _ = try? await ApiClient.shared.setLanguage(token: token,
                                                           code: language) }
    }

    private func load() async {
        guard let token = state.token else { return }
        loading = true
        count = (try? await ApiClient.shared.keys(token: token))?.count
        intact = (try? await ApiClient.shared.auditVerify(token: token))?.intact
        loading = false
        languages = (try? await ApiClient.shared.languages())?.languages ?? []
        if let token = state.token,
           let l = try? await ApiClient.shared.language(token: token) {
            language = l.language
        }
    }
}
