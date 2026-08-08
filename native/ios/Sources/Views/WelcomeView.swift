import SwiftUI

/// First-run: paste the tenant vault token + base URL, validated via GET /records.
struct WelcomeView: View {
    @EnvironmentObject var state: AppState
    @State private var token = ""
    @State private var language = "en"
    private let languageChoices = [
        ("en", "English"), ("es", "Español"), ("fr", "Français"),
        ("de", "Deutsch"), ("pt", "Português"), ("it", "Italiano"),
        ("ja", "日本語"), ("zh", "中文"), ("hi", "हिन्दी"), ("ar", "العربية"),
    ]
    @State private var base = "http://127.0.0.1:8000"
    /// Held in view state and handed to the client, never to
    /// `UserDefaults` — see `ApiClient.holdKey`.
    @State private var tenantKey = ""
    @State private var busy = false
    @State private var error: String?

    /// Nobody reading this screen has an account, so there is no stored
    /// language to take. `AppState.language` would be "en" for every
    /// reader on earth; the device knows better and always did.
    private let lang = L10n.deviceLanguage

    var body: some View {
        ScrollView {
            VStack(spacing: 22) {
                Circle()
                    .fill(Theme.brand)
                    .frame(width: 84, height: 84)
                    .overlay(Image(systemName: "lock.shield").font(.system(size: 34)).foregroundStyle(.white))
                    .shadow(color: Theme.brandA.opacity(0.5), radius: 24, y: 8)
                    .padding(.top, 40)

                VStack(spacing: 6) {
                    Text(L10n.t("wel.title", lang)).font(.title2.bold()).foregroundStyle(Theme.txt)
                    Text(L10n.t("wel.sub", lang))
                        .font(.footnote).foregroundStyle(Theme.t2)
                        .multilineTextAlignment(.center)
                }

                VStack(alignment: .leading, spacing: 14) {
                    field(L10n.t("wel.token", lang)) {
                        SecureField("pdi_…", text: $token).textFieldStyle(.plain).foregroundStyle(Theme.txt)
                            .textInputAutocapitalization(.never).autocorrectionDisabled()
                    }
                    field(L10n.t("wel.server", lang)) {
                        TextField("http://127.0.0.1:8000", text: $base).textFieldStyle(.plain).foregroundStyle(Theme.txt)
                            .textInputAutocapitalization(.never).autocorrectionDisabled()
                    }
                    // Only a vault under customer custody needs this, which
                    // is why it is optional and says so. Leaving it blank on
                    // such a vault is what every phone did until now, and
                    // every record answered 428.
                    field(L10n.t("wel.tenantkey", lang)) {
                        SecureField(L10n.t("wel.tenantkey.ph", lang), text: $tenantKey)
                            .textFieldStyle(.plain).foregroundStyle(Theme.txt)
                            .textInputAutocapitalization(.never).autocorrectionDisabled()
                    }
                    field(L10n.t("wel.language", lang)) {
                        Picker("", selection: $language) {
                            ForEach(languageChoices, id: \.0) { code, label in
                                Text(label).tag(code)
                            }
                        }.pickerStyle(.menu).tint(Theme.brandA)
                    }
                }.card()

                if let error { Text(error).font(.footnote).foregroundStyle(Theme.red) }

                Button(action: signIn) {
                    HStack { if busy { ProgressView().tint(.white) }; Text(L10n.t("wel.unlock", lang)).bold() }
                        .frame(maxWidth: .infinity).padding(.vertical, 14)
                        .background(Theme.brand).foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 13))
                }
                .disabled(token.isEmpty || busy)
                .opacity(token.isEmpty ? 0.5 : 1)

                Text(L10n.t("wel.backend", lang)
                    + "  PDI_CORS_ORIGINS=* uvicorn pdi.api:app")
                    .font(.system(size: 10, design: .monospaced)).foregroundStyle(Theme.t3)
            }.padding(20)
        }
    }

    private func field<Content: View>(_ label: String, @ViewBuilder _ content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label).font(.caption).foregroundStyle(Theme.t2)
            content()
                .padding(.horizontal, 12).padding(.vertical, 10)
                .background(Theme.scrBot).clipShape(RoundedRectangle(cornerRadius: 11))
                .overlay(RoundedRectangle(cornerRadius: 11).stroke(Theme.line, lineWidth: 1))
        }
    }

    private func signIn() {
        busy = true; error = nil
        Task {
            await ApiClient.shared.setBase(base)
            // Before the validating call, not after: on a vault under
            // customer custody the validation itself needs the key.
            await ApiClient.shared.holdKey(tenantKey)
            do {
                _ = try await ApiClient.shared.keys(token: token)   // 200 == valid token
                if language != "en" {
                    _ = try? await ApiClient.shared.setLanguage(token: token,
                                                                code: language)
                }
                state.signIn(token: token, base: base)
            } catch {
                self.error = "Couldn't unlock — check the token and server. (\(error.localizedDescription))"
            }
            busy = false
        }
    }
}
