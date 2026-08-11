import SwiftUI

/// Compliance-grade secure transfer, both directions: **Outbound** seals a
/// file for a recipient (one-shot receive token); **Intake** requests a file
/// in from a counterparty (one-shot submit token), with an "act as sender"
/// form to exercise the loop end to end.
struct TransfersView: View {
    @EnvironmentObject var state: AppState

    enum Direction: String, CaseIterable {
        case outbound = "Outbound", intake = "Intake"

        /// The raw value is what the screen switches on; this is what a
        /// person reads. Keeping the two apart is the rule the picker
        /// round settled — a localized raw value is a control that
        /// quietly stops matching.
        var key: String {
            switch self {
            case .outbound: return "ntr.t.outbound"
            case .intake:   return "ntr.t.intake"
            }
        }
    }
    @State private var direction: Direction = .outbound

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Picker("", selection: $direction) {
                    ForEach(Direction.allCases, id: \.self) { Text(L10n.t($0.key, state.language)).tag($0) }
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
                Text(L10n.t("tab.transfers", state.language)).font(.title2.bold()).foregroundStyle(Theme.txt)
                Text(L10n.t("nfil.sub", state.language))
                    .font(.footnote).foregroundStyle(Theme.t2)

                VStack(alignment: .leading, spacing: 10) {
                    field(L10n.t("nfil.recipient", state.language)) { TextField(L10n.t("nfil.recipient.ph", state.language), text: $recipient)
                        .foregroundStyle(Theme.txt).textInputAutocapitalization(.never) }
                    field(L10n.t("nfil.filename", state.language)) { TextField(L10n.t("nfil.filename.ph", state.language), text: $filename)
                        .foregroundStyle(Theme.txt).textInputAutocapitalization(.never) }
                    field(L10n.t("nfil.content", state.language)) { TextField(L10n.t("nfil.content.ph", state.language), text: $content, axis: .vertical)
                        .lineLimit(1...3).foregroundStyle(Theme.txt) }
                    Text(L10n.t("nfil.programs", state.language)).font(.caption).foregroundStyle(Theme.t2)
                    FlowChips(programs: programs, selected: $selected)
                    Button(action: create) {
                        HStack { if busy { ProgressView().tint(.white) }; Text(L10n.t("nfil.seal", state.language)).bold() }
                            .frame(maxWidth: .infinity).padding(.vertical, 12)
                            .background(Theme.brand).foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                    }.disabled(recipient.isEmpty || filename.isEmpty || content.isEmpty
                               || selected.isEmpty || busy)
                }.card()

                if let error { Text(error).font(.footnote).foregroundStyle(Theme.red) }

                if let mintedToken {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(L10n.t("nfil.token.once", state.language)).font(.headline).foregroundStyle(Theme.amber)
                        Text(mintedToken).font(.system(.caption, design: .monospaced))
                            .foregroundStyle(Theme.txt)
                        Text(L10n.t("nfil.token.hand", state.language))
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
                            Text(L10n.t("ntr.retained", state.language).replacingOccurrences(of: "{date}", with: exp)).font(.caption2).foregroundStyle(Theme.t3)
                        }
                        if t.status != "revoked" {
                            Button(L10n.t("ntr.revoke", state.language)) { revoke(t) }
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
    // L10n.t("ntr.as.sender", state.language) demo form
    @State private var senderToken = ""
    @State private var senderFile = ""
    @State private var senderContent = ""
    @State private var received: [String: IntakeFile] = [:]
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(L10n.t("ntr.intake", state.language)).font(.title2.bold()).foregroundStyle(Theme.txt)
            Text(L10n.t("ntr.intake.sub", state.language))
                .font(.footnote).foregroundStyle(Theme.t2)

            VStack(alignment: .leading, spacing: 10) {
                field(L10n.t("nreq.from", state.language)) { TextField(L10n.t("nreq.from.ph", state.language), text: $fromParty)
                    .foregroundStyle(Theme.txt).textInputAutocapitalization(.never) }
                field(L10n.t("nreq.purpose", state.language)) { TextField(L10n.t("nreq.purpose.ph", state.language), text: $purpose)
                    .foregroundStyle(Theme.txt) }
                Text(L10n.t("nfil.programs", state.language)).font(.caption).foregroundStyle(Theme.t2)
                FlowChips(programs: programs, selected: $selected)
                Button(action: create) {
                    HStack { if busy { ProgressView().tint(.white) }; Text(L10n.t("nreq.go", state.language)).bold() }
                        .frame(maxWidth: .infinity).padding(.vertical, 12)
                        .background(Theme.brand).foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }.disabled(fromParty.isEmpty || selected.isEmpty || busy)
            }.card()

            if let error { Text(error).font(.footnote).foregroundStyle(Theme.red) }

            if let mintedToken {
                VStack(alignment: .leading, spacing: 6) {
                    Text(L10n.t("nint.token.once", state.language)).font(.headline).foregroundStyle(Theme.amber)
                    Text(mintedToken).font(.system(.caption, design: .monospaced))
                        .foregroundStyle(Theme.txt)
                    Text(L10n.t("nint.token.send", state.language))
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
                        Button(L10n.t("ntr.read", state.language)) { read(i) }
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
                        Button(L10n.t("nreq.close", state.language)) { close(i) }
                            .font(.caption.bold()).foregroundStyle(Theme.red)
                    }
                }.card()
            }

            // The counterparty's side, for exercising the loop on-device.
            VStack(alignment: .leading, spacing: 10) {
                Text(L10n.t("ntr.as.sender", state.language)).font(.headline).foregroundStyle(Theme.txt)
                Text(L10n.t("ntr.answer.sub", state.language))
                    .font(.caption).foregroundStyle(Theme.t2)
                field(L10n.t("nint.token", state.language)) { TextField(L10n.t("nint.token.ph", state.language), text: $senderToken)
                    .foregroundStyle(Theme.txt).textInputAutocapitalization(.never) }
                field(L10n.t("nfil.filename", state.language)) { TextField(L10n.t("nint.filename.ph", state.language), text: $senderFile)
                    .foregroundStyle(Theme.txt).textInputAutocapitalization(.never) }
                field(L10n.t("nfil.content", state.language)) { TextField(L10n.t("nint.content.ph", state.language), text: $senderContent)
                    .foregroundStyle(Theme.txt) }
                Button(L10n.t("nint.go", state.language)) { submit() }
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
