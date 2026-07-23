import SwiftUI

/// First-run: paste the tenant vault token + base URL, validated via GET /records.
struct WelcomeView: View {
    @EnvironmentObject var state: AppState
    @State private var token = ""
    @State private var base = "http://127.0.0.1:8000"
    @State private var busy = false
    @State private var error: String?

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
                    Text("Sign in to your vault").font(.title2.bold()).foregroundStyle(Theme.txt)
                    Text("Paste the tenant token you were issued. It authorizes every call and never leaves this device unencrypted in transit.")
                        .font(.footnote).foregroundStyle(Theme.t2)
                        .multilineTextAlignment(.center)
                }

                VStack(alignment: .leading, spacing: 14) {
                    field("Vault token") {
                        SecureField("pdi_…", text: $token).textFieldStyle(.plain).foregroundStyle(Theme.txt)
                            .textInputAutocapitalization(.never).autocorrectionDisabled()
                    }
                    field("Server") {
                        TextField("http://127.0.0.1:8000", text: $base).textFieldStyle(.plain).foregroundStyle(Theme.txt)
                            .textInputAutocapitalization(.never).autocorrectionDisabled()
                    }
                }.card()

                if let error { Text(error).font(.footnote).foregroundStyle(Theme.red) }

                Button(action: signIn) {
                    HStack { if busy { ProgressView().tint(.white) }; Text("Unlock").bold() }
                        .frame(maxWidth: .infinity).padding(.vertical, 14)
                        .background(Theme.brand).foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 13))
                }
                .disabled(token.isEmpty || busy)
                .opacity(token.isEmpty ? 0.5 : 1)

                Text("Start the backend:  PDI_CORS_ORIGINS=* uvicorn pdi.api:app")
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
            do {
                _ = try await ApiClient.shared.keys(token: token)   // 200 == valid token
                state.signIn(token: token, base: base)
            } catch {
                self.error = "Couldn't unlock — check the token and server. (\(error.localizedDescription))"
            }
            busy = false
        }
    }
}
