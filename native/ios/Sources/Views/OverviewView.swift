import SwiftUI

/// Dashboard: record count + audit integrity, pulled from the live vault.
struct OverviewView: View {
    @EnvironmentObject var state: AppState
    @State private var count: Int?
    @State private var intact: Bool?
    @State private var loading = true
    @State private var languages: [LanguageInfo] = []
    @State private var language = "en"
    @State private var preTranslate = true

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                HStack(spacing: 8) {
                    Circle().fill(Theme.green).frame(width: 8, height: 8)
                    OfflinePostureCard()
                    Text(L10n.t("nov.unlocked", state.language)).font(.caption.bold()).foregroundStyle(Theme.green)
                }
                Text(L10n.t("nov.title", state.language)).font(.title.bold()).foregroundStyle(Theme.txt)
                Text(L10n.t("nov.sealed", state.language))
                    .font(.subheadline).foregroundStyle(Theme.t2)

                HStack(spacing: 12) {
                    stat(L10n.t("nrec.t.records", state.language), loading ? "—" : "\(count ?? 0)", Theme.brandA)
                    stat(L10n.t("tab.audit", state.language), loading ? "—" : (intact == true ? L10n.t("nov.intact", state.language) : L10n.t("nov.broken", state.language)),
                         intact == false ? Theme.red : Theme.green)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text(L10n.t("nov.token", state.language)).font(.headline).foregroundStyle(Theme.txt)
                    Text(masked(state.token ?? "")).font(.system(.subheadline, design: .monospaced))
                        .foregroundStyle(Theme.t2)
                    Text(state.baseURL).font(.caption).foregroundStyle(Theme.t3)
                }.card()

                VStack(alignment: .leading, spacing: 8) {
                    Text(L10n.t("wel.language", state.language))
                        .font(.headline).foregroundStyle(Theme.txt)
                    Text(L10n.t("nov.notes", state.language))
                        .font(.caption).foregroundStyle(Theme.t2)
                    Picker("", selection: $language) {
                        ForEach(languages, id: \.code) { l in
                            Text(l.label + (l.notes_translated == true
                                            ? "" : " (notes in English)")).tag(l.code)
                        }
                    }
                    .pickerStyle(.menu).tint(Theme.brandA)
                    .onChange(of: language) { _ in applyLanguage() }
                    Toggle(isOn: $preTranslate) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(L10n.t("nov.pretrans", state.language))
                                .font(.subheadline).foregroundStyle(Theme.txt)
                            Text(L10n.t("nov.pretrans.off", state.language))
                                .font(.caption2).foregroundStyle(Theme.t2)
                        }
                    }
                    .tint(Theme.green)
                    .onChange(of: preTranslate) { _ in applyLanguage() }
                }.card()

                ImproveCard()

                AccessCard()

                AdminCard()
                TenantsAdminCard()
                GateCard()
                ContinuityCard()

                Button(L10n.t("action.sign_out", state.language)) { state.signOut() }
                    .font(.subheadline).foregroundStyle(Theme.t2)
                    .frame(maxWidth: .infinity).padding(.vertical, 12)
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(Theme.line, lineWidth: 1))
            }.padding(20)
        }
        .refreshable { await load() }
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
        state.rememberLanguage(language)
        Task {
            _ = try? await ApiClient.shared.setLanguage(
                token: token, code: language,
                mode: preTranslate ? "pre" : "on_demand")
        }
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
            preTranslate = (l.mode ?? "pre") == "pre"
            state.rememberLanguage(l.language)   // chrome follows the tenant
        }
    }
}
