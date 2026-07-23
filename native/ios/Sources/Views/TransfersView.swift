import SwiftUI

/// Compliance-grade secure transfer, both directions: **Outbound** seals a
/// file for a recipient (one-shot receive token); **Intake** requests a file
/// in from a counterparty (one-shot submit token), with an "act as sender"
/// form to exercise the loop end to end.
struct TransfersView: View {
    enum Direction: String, CaseIterable { case outbound = "Outbound", intake = "Intake" }
    @State private var direction: Direction = .outbound

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Picker("", selection: $direction) {
                    ForEach(Direction.allCases, id: \.self) { Text($0.rawValue).tag($0) }
                }.pickerStyle(.segmented)

                switch direction {
                case .outbound: OutboundSection()
                case .intake: IntakeSection()
                }
            }.padding(20)
        }
    }
}

private struct OutboundSection: View {
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

// MARK: Intake — request a file in; the sender submits with a one-shot token

private struct IntakeSection: View {
    @EnvironmentObject var state: AppState
    @State private var programs: [ComplianceProgram] = []
    @State private var selected: Set<String> = ["hipaa"]
    @State private var fromParty = ""
    @State private var purpose = ""
    @State private var intakes: [Intake] = []
    @State private var mintedToken: String?
    // "Act as the sender" demo form
    @State private var senderToken = ""
    @State private var senderFile = ""
    @State private var senderContent = ""
    @State private var received: [String: IntakeFile] = [:]
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Secure intake").font(.title2.bold()).foregroundStyle(Theme.txt)
            Text("Ask a counterparty to send a file in. They authenticate with the one-shot submit token — no account needed.")
                .font(.footnote).foregroundStyle(Theme.t2)

            VStack(alignment: .leading, spacing: 10) {
                field("From") { TextField("who should send it", text: $fromParty)
                    .foregroundStyle(Theme.txt).textInputAutocapitalization(.never) }
                field("Purpose (optional)") { TextField("why you need it", text: $purpose)
                    .foregroundStyle(Theme.txt) }
                Text("Programs").font(.caption).foregroundStyle(Theme.t2)
                FlowChips(programs: programs, selected: $selected)
                Button(action: create) {
                    HStack { if busy { ProgressView().tint(.white) }; Text("Request file").bold() }
                        .frame(maxWidth: .infinity).padding(.vertical, 12)
                        .background(Theme.brand).foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }.disabled(fromParty.isEmpty || selected.isEmpty || busy)
            }.card()

            if let error { Text(error).font(.footnote).foregroundStyle(Theme.red) }

            if let mintedToken {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Submit token — shown once").font(.headline).foregroundStyle(Theme.amber)
                    Text(mintedToken).font(.system(.caption, design: .monospaced))
                        .foregroundStyle(Theme.txt)
                    Text("Send this to the counterparty out of band; it is their only way in.")
                        .font(.caption).foregroundStyle(Theme.t2)
                }.card()
            }

            ForEach(intakes, id: \.id) { i in
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text(i.from_party).font(.subheadline.bold()).foregroundStyle(Theme.txt)
                        Spacer()
                        Text(i.status.capitalized).font(.caption)
                            .foregroundStyle(i.status == "submitted" ? Theme.green : Theme.t2)
                    }
                    if let p = i.purpose {
                        Text(p).font(.caption).foregroundStyle(Theme.t2)
                    }
                    Text(i.programs.map { $0.uppercased() }.joined(separator: " "))
                        .font(.caption2).foregroundStyle(Theme.t3)
                    if i.status == "submitted" {
                        Button("Read sealed file") { read(i) }
                            .font(.caption.bold()).foregroundStyle(Theme.brandA)
                        if let f = received[i.id] {
                            Text("\(f.filename ?? "file"): \(f.content ?? "")")
                                .font(.system(.caption, design: .monospaced))
                                .foregroundStyle(Theme.t2)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(8).background(Theme.scrBot)
                                .clipShape(RoundedRectangle(cornerRadius: 9))
                        }
                    }
                    if i.status == "open" {
                        Button("Close request") { close(i) }
                            .font(.caption.bold()).foregroundStyle(Theme.red)
                    }
                }.card()
            }

            // The counterparty's side, for exercising the loop on-device.
            VStack(alignment: .leading, spacing: 10) {
                Text("Act as the sender").font(.headline).foregroundStyle(Theme.txt)
                Text("Paste an intake's submit token to answer it — this is what the counterparty does, no vault account involved.")
                    .font(.caption).foregroundStyle(Theme.t2)
                field("Submit token") { TextField("intk token", text: $senderToken)
                    .foregroundStyle(Theme.txt).textInputAutocapitalization(.never) }
                field("Filename") { TextField("e.g. w2.pdf", text: $senderFile)
                    .foregroundStyle(Theme.txt).textInputAutocapitalization(.never) }
                field("Content") { TextField("the file body", text: $senderContent)
                    .foregroundStyle(Theme.txt) }
                Button("Submit into the newest open intake") { submit() }
                    .font(.caption.bold()).foregroundStyle(.white)
                    .frame(maxWidth: .infinity).padding(.vertical, 10)
                    .background(Theme.brandA).clipShape(RoundedRectangle(cornerRadius: 11))
                    .disabled(senderToken.isEmpty || senderFile.isEmpty || senderContent.isEmpty)
            }.card()
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
        intakes = (try? await ApiClient.shared.intakes(token: token)) ?? []
    }

    private func create() {
        guard let token = state.token else { return }
        busy = true; error = nil
        Task {
            do {
                let i = try await ApiClient.shared.createIntake(
                    token: token, fromParty: fromParty, purpose: purpose,
                    programs: Array(selected))
                mintedToken = i.submit_token
                fromParty = ""; purpose = ""
            } catch { self.error = error.localizedDescription }
            await load(); busy = false
        }
    }

    private func read(_ intake: Intake) {
        guard let token = state.token else { return }
        Task {
            if let f = try? await ApiClient.shared.intakeFile(token: token, iid: intake.id) {
                received[intake.id] = f
            }
        }
    }

    private func close(_ intake: Intake) {
        guard let token = state.token else { return }
        Task {
            try? await ApiClient.shared.closeIntake(token: token, iid: intake.id)
            await load()
        }
    }

    private func submit() {
        guard let target = intakes.last(where: { $0.status == "open" }) else {
            error = "no open intake to submit into"; return
        }
        error = nil
        Task {
            do {
                try await ApiClient.shared.submitIntake(
                    iid: target.id, submitToken: senderToken,
                    filename: senderFile, content: senderContent)
                senderToken = ""; senderFile = ""; senderContent = ""
                await load()
            } catch { self.error = error.localizedDescription }
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
