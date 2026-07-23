import SwiftUI

/// Compliance-grade secure transfers: seal a file for a recipient under one or
/// more programs (HIPAA, CPNI, …). The one-shot receive token is shown exactly
/// once; retention follows the strictest selected program.
struct TransfersView: View {
    @EnvironmentObject var state: AppState
    @State private var programs: [ComplianceProgram] = []
    @State private var selected: Set<String> = ["hipaa"]
    @State private var recipient = ""
    @State private var filename = ""
    @State private var content = ""
    @State private var transfers: [Transfer] = []
    @State private var mintedToken: String?
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Transfers").font(.title2.bold()).foregroundStyle(Theme.txt)
                Text("Seal a file for a recipient under compliance controls. Retention follows the strictest program you pick.")
                    .font(.footnote).foregroundStyle(Theme.t2)

                VStack(alignment: .leading, spacing: 10) {
                    field("Recipient") { TextField("who it's for", text: $recipient)
                        .foregroundStyle(Theme.txt).textInputAutocapitalization(.never) }
                    field("Filename") { TextField("e.g. results.pdf", text: $filename)
                        .foregroundStyle(Theme.txt).textInputAutocapitalization(.never) }
                    field("Content") { TextField("the file body to seal", text: $content, axis: .vertical)
                        .lineLimit(1...3).foregroundStyle(Theme.txt) }
                    Text("Programs").font(.caption).foregroundStyle(Theme.t2)
                    FlowChips(programs: programs, selected: $selected)
                    Button(action: create) {
                        HStack { if busy { ProgressView().tint(.white) }; Text("Seal & create").bold() }
                            .frame(maxWidth: .infinity).padding(.vertical, 12)
                            .background(Theme.brand).foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                    }.disabled(recipient.isEmpty || filename.isEmpty || content.isEmpty
                               || selected.isEmpty || busy)
                }.card()

                if let error { Text(error).font(.footnote).foregroundStyle(Theme.red) }

                if let mintedToken {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Receive token — shown once").font(.headline).foregroundStyle(Theme.amber)
                        Text(mintedToken).font(.system(.caption, design: .monospaced))
                            .foregroundStyle(Theme.txt)
                        Text("Hand this to the recipient out of band; it is the only way to retrieve the file.")
                            .font(.caption).foregroundStyle(Theme.t2)
                    }.card()
                }

                ForEach(transfers, id: \.id) { t in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text(t.filename).font(.subheadline.bold()).foregroundStyle(Theme.txt)
                            Spacer()
                            Text(t.status.capitalized).font(.caption)
                                .foregroundStyle(t.status == "revoked" ? Theme.red : Theme.green)
                        }
                        Text("→ \(t.recipient) · \(t.programs.map { $0.uppercased() }.joined(separator: " "))")
                            .font(.caption).foregroundStyle(Theme.t2)
                        if let exp = t.expires_at {
                            Text("retained until \(exp)").font(.caption2).foregroundStyle(Theme.t3)
                        }
                        if t.status != "revoked" {
                            Button("Revoke access") { revoke(t) }
                                .font(.caption.bold()).foregroundStyle(Theme.red)
                        }
                    }.card()
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
        programs = (try? await ApiClient.shared.compliancePrograms(token: token))?.programs ?? []
        transfers = (try? await ApiClient.shared.transfers(token: token)) ?? []
    }

    private func create() {
        guard let token = state.token else { return }
        busy = true; error = nil
        Task {
            do {
                let t = try await ApiClient.shared.createTransfer(
                    token: token, recipient: recipient, filename: filename,
                    content: content, programs: Array(selected))
                mintedToken = t.receive_token
                recipient = ""; filename = ""; content = ""
            } catch { self.error = error.localizedDescription }
            await load(); busy = false
        }
    }

    private func revoke(_ t: Transfer) {
        guard let token = state.token else { return }
        Task {
            try? await ApiClient.shared.revokeTransfer(token: token, tid: t.id)
            await load()
        }
    }
}

/// Wrapping chip rows for compliance-program selection.
private struct FlowChips: View {
    let programs: [ComplianceProgram]
    @Binding var selected: Set<String>

    var body: some View {
        let rows = programs.chunked(4)
        VStack(alignment: .leading, spacing: 6) {
            ForEach(0..<rows.count, id: \.self) { i in
                HStack(spacing: 6) {
                    ForEach(rows[i], id: \.key) { p in
                        let on = selected.contains(p.key)
                        Text(p.key.uppercased())
                            .font(.caption2.bold())
                            .padding(.horizontal, 9).padding(.vertical, 6)
                            .background(on ? Theme.brandA : Theme.card)
                            .foregroundStyle(on ? .white : Theme.t2)
                            .clipShape(Capsule())
                            .onTapGesture {
                                if on { selected.remove(p.key) } else { selected.insert(p.key) }
                            }
                    }
                }
            }
        }
    }
}

private extension Array {
    func chunked(_ size: Int) -> [[Element]] {
        stride(from: 0, to: count, by: size).map {
            Array(self[$0..<Swift.min($0 + size, count)])
        }
    }
}
