import SwiftUI

/// The record store: list keys, add a sealed record, reveal or delete one.
struct VaultView: View {
    @EnvironmentObject var state: AppState
    @State private var keys: [String] = []
    @State private var newKey = ""
    @State private var newValue = ""
    @State private var revealed: [String: String] = [:]
    @State private var loading = true
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Vault").font(.title2.bold()).foregroundStyle(Theme.txt)
                Text("Store a value — it is sealed at rest with AES-256-GCM.")
                    .font(.footnote).foregroundStyle(Theme.t2)

                VStack(alignment: .leading, spacing: 10) {
                    field("Key") { TextField("e.g. ssn", text: $newKey).foregroundStyle(Theme.txt)
                        .textInputAutocapitalization(.never).autocorrectionDisabled() }
                    field("Value") { TextField("plaintext to seal", text: $newValue, axis: .vertical)
                        .lineLimit(1...3).foregroundStyle(Theme.txt) }
                    Button(action: put) {
                        HStack { if busy { ProgressView().tint(.white) }; Text("Seal record").bold() }
                            .frame(maxWidth: .infinity).padding(.vertical, 12)
                            .background(Theme.brand).foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                    }.disabled(newKey.isEmpty || newValue.isEmpty || busy)
                }.card()

                if let error { Text(error).font(.footnote).foregroundStyle(Theme.red) }

                if loading {
                    ProgressView().tint(Theme.brandA).frame(maxWidth: .infinity)
                } else if keys.isEmpty {
                    Text("No records yet — seal one above.").font(.footnote).foregroundStyle(Theme.t2).card()
                } else {
                    ForEach(keys, id: \.self) { key in
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Image(systemName: "key.fill").font(.caption).foregroundStyle(Theme.brandA)
                                Text(key).font(.subheadline.bold()).foregroundStyle(Theme.txt)
                                Spacer()
                                Button(revealed[key] == nil ? "Reveal" : "Hide") { toggle(key) }
                                    .font(.caption).foregroundStyle(Theme.brandA)
                                Button { remove(key) } label: {
                                    Image(systemName: "trash").font(.caption).foregroundStyle(Theme.red)
                                }
                            }
                            if let v = revealed[key] {
                                Text(v).font(.system(.footnote, design: .monospaced))
                                    .foregroundStyle(Theme.t2)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .padding(10).background(Theme.scrBot)
                                    .clipShape(RoundedRectangle(cornerRadius: 9))
                            }
                        }.card()
                    }
                }
            }.padding(20)
        }
        .task { await load() }
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

    private func load() async {
        guard let token = state.token else { return }
        loading = true
        keys = (try? await ApiClient.shared.keys(token: token)) ?? []
        loading = false
    }

    private func put() {
        guard let token = state.token else { return }
        busy = true; error = nil
        Task {
            do {
                try await ApiClient.shared.putRecord(token: token, key: newKey, value: newValue)
                newKey = ""; newValue = ""
                await load()
            } catch { self.error = error.localizedDescription }
            busy = false
        }
    }

    private func toggle(_ key: String) {
        if revealed[key] != nil { revealed[key] = nil; return }
        guard let token = state.token else { return }
        Task {
            if let rec = try? await ApiClient.shared.record(token: token, key: key) {
                revealed[key] = rec.value
            }
        }
    }

    private func remove(_ key: String) {
        guard let token = state.token else { return }
        Task {
            try? await ApiClient.shared.deleteRecord(token: token, key: key)
            revealed[key] = nil
            await load()
        }
    }
}
