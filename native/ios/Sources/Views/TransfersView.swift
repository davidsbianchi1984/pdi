import SwiftUI

/// Compliance-grade secure transfer, both directions: **Outbound** seals a
/// file for a recipient (one-shot receive token); **Intake** requests a file
/// in from a counterparty (one-shot submit token), with an "act as sender"
/// form to exercise the loop end to end.
struct TransfersView: View {
    @EnvironmentObject var state: AppState

    enum Direction: String, CaseIterable {
        // "carriers" lowercase on purpose: the raw value is what the screen
        // switches on, never what a person reads — and the capitalized word
        // is one the table translates, which the language guard rightly
        // reads as English shown untranslated.
        case outbound = "Outbound", intake = "Intake", carriers = "carriers"

        /// The raw value is what the screen switches on; this is what a
        /// person reads. Keeping the two apart is the rule the picker
        /// round settled — a localized raw value is a control that
        /// quietly stops matching.
        var key: String {
            switch self {
            case .outbound: return "ntr.t.outbound"
            case .intake:   return "ntr.t.intake"
            case .carriers: return "car.title"
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
                case .carriers: CarriersSection()
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
    @State private var linkOk: String?

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
                        HStack(spacing: 10) {
                            // Resolve the recipient's page before the link
                            // goes into an email — a misconfigured public
                            // base is otherwise discovered by the recipient,
                            // who has nobody to ask.
                            Button(L10n.t("ntr.reciplink", state.language)) {
                                checkLink(t.id)
                            }
                            .font(.caption2).foregroundStyle(Theme.brandA)
                            if linkOk == t.id {
                                Text(L10n.t("car.verifies", state.language))
                                    .font(.caption2).foregroundStyle(Theme.green)
                            }
                            if t.status != "revoked" {
                                Button(L10n.t("ntr.revoke", state.language)) { revoke(t) }
                                    .font(.caption.bold()).foregroundStyle(Theme.red)
                            }
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

    private func checkLink(_ tid: String) {
        Task {
            if (try? await ApiClient.shared.checkRecipientPage(tid: tid)) == true {
                linkOk = tid
            } else {
                error = L10n.t("car.notverify", state.language)
            }
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

// MARK: carriers — the sticker on the sealed thing, and everyone who rang it

/// The console's Carriers screen, on the phone: place a custody code,
/// advance its state, read its chain, see what a scanner sees, and answer
/// as the scanner — found and ring — plus the pairing card, because the QR
/// on this screen is how the phone got here in the first place.
private struct CarriersSection: View {
    @EnvironmentObject var state: AppState
    @State private var rows: [CarrierBeacon] = []
    @State private var rings: [RingRow] = []
    @State private var label = ""
    @State private var disclose = "blind"
    @State private var card: ScanCardOut?
    @State private var custody: CustodyChainOut?
    @State private var transcript: RingRow?
    @State private var pair: PairInfoOut?
    @State private var busy = false
    @State private var error: String?

    private let states = ["sealed", "in_transit", "delivered", "opened"]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(L10n.t("car.title", state.language))
                .font(.title2.bold()).foregroundStyle(Theme.txt)

            // Place a code on a thing.
            VStack(alignment: .leading, spacing: 10) {
                Text(L10n.t("car.place", state.language))
                    .font(.subheadline.bold()).foregroundStyle(Theme.txt)
                TextField(L10n.t("car.label.ph", state.language), text: $label)
                    .foregroundStyle(Theme.txt)
                HStack(spacing: 8) {
                    ForEach(["blind", "contact"], id: \.self) { d in
                        Button(L10n.t("car.disclose.\(d)", state.language)) {
                            disclose = d
                        }
                        .font(.caption2)
                        .foregroundStyle(disclose == d ? .white : Theme.t2)
                        .padding(.horizontal, 10).padding(.vertical, 5)
                        .background(disclose == d ? Theme.brandA : Theme.scrBot)
                        .clipShape(Capsule())
                    }
                    Button(L10n.t("car.place.go", state.language)) { place() }
                        .font(.caption.bold()).foregroundStyle(.white)
                        .padding(.horizontal, 12).padding(.vertical, 7)
                        .background(Theme.brandA).clipShape(Capsule())
                        .disabled(busy || label.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }.card()

            if let error { Text(error).font(.caption).foregroundStyle(Theme.red) }
            if rows.isEmpty {
                Text(L10n.t("car.none", state.language))
                    .font(.caption).foregroundStyle(Theme.t2)
            }

            ForEach(rows, id: \.id) { row in
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text(row.label).font(.subheadline.bold()).foregroundStyle(Theme.txt)
                        Spacer()
                        Text("\(row.ref_kind) · \(row.state) · \(row.disclose) · ×\(row.scans)"
                             + (row.active ? "" : " · " + L10n.t("car.lifted", state.language)))
                            .font(.caption2).foregroundStyle(Theme.t2)
                    }
                    HStack(spacing: 10) {
                        Button(L10n.t("car.chain", state.language)) { chain(row.id) }
                        Button(L10n.t("car.sees", state.language)) { sees(row.id) }
                        Button(L10n.t("car.refresh", state.language)) { refresh(row.id) }
                        // The state select, as a walk along the chain.
                        Menu(row.state) {
                            ForEach(states, id: \.self) { st in
                                Button(st) { setState(row.id, st) }
                            }
                        }.font(.caption2)
                        Button(L10n.t("car.lift", state.language)) { lift(row.id) }
                            .foregroundStyle(Theme.red)
                    }
                    .font(.caption2).foregroundStyle(Theme.brandA)
                    .disabled(busy)
                    // The scanner's half, exercised from here: found and ring
                    // take no bearer at all.
                    HStack(spacing: 10) {
                        Button(L10n.t("car.ring", state.language)) { ring(row.id) }
                        Button(L10n.t("car.found", state.language)) { found(row.id) }
                    }
                    .font(.caption2).foregroundStyle(Theme.brandA)
                    .disabled(busy)
                    Text(L10n.t("qr.addr", state.language) + " "
                         + ApiClient.shared.scanQrUrl(bid: row.id).absoluteString)
                        .font(.caption2.monospaced()).foregroundStyle(Theme.t3)
                        .textSelection(.enabled)
                    Text(ApiClient.shared.scanPageUrl(bid: row.id).absoluteString)
                        .font(.caption2.monospaced()).foregroundStyle(Theme.t3)
                        .textSelection(.enabled)
                }.card()
            }

            if let card {
                VStack(alignment: .leading, spacing: 6) {
                    Text(L10n.t("car.strangercard", state.language))
                        .font(.subheadline.bold()).foregroundStyle(Theme.txt)
                    Text(card.badge).font(.caption.bold()).foregroundStyle(Theme.txt)
                    Text(card.note).font(.caption2).foregroundStyle(Theme.t2)
                    Text("\(card.reference) · \(card.kind) · \(card.state) · "
                         + L10n.t(card.under_custody ? "car.custody.yes"
                                                     : "car.custody.no",
                                  state.language))
                        .font(.caption2).foregroundStyle(Theme.t2)
                    Text(L10n.t("car.contents", state.language) + " "
                         + L10n.t("car.contents.no", state.language) + " "
                         + L10n.t("car.contents.never", state.language))
                        .font(.caption2).foregroundStyle(Theme.t3)
                }.card()
            }

            if let custody {
                VStack(alignment: .leading, spacing: 6) {
                    Text(L10n.t("car.chain", state.language))
                        .font(.subheadline.bold()).foregroundStyle(Theme.txt)
                    Text(L10n.t("car.auditchain", state.language) + " "
                         + L10n.t(custody.audit_chain_intact ? "car.verifies"
                                                             : "car.notverify",
                                  state.language))
                        .font(.caption2).foregroundStyle(Theme.t2)
                    ForEach(Array(custody.chain_of_custody.enumerated()),
                            id: \.offset) { _, e in
                        Text("\(e.event) — \(e.actor) · \(e.at)")
                            .font(.caption2).foregroundStyle(Theme.t2)
                    }
                }.card()
            }

            // Who rang: every scanner who pressed the sticker's button.
            VStack(alignment: .leading, spacing: 6) {
                Text(L10n.t("car.rang", state.language))
                    .font(.subheadline.bold()).foregroundStyle(Theme.txt)
                if rings.isEmpty {
                    Text(L10n.t("car.norings", state.language))
                        .font(.caption2).foregroundStyle(Theme.t2)
                }
                ForEach(rings, id: \.id) { r in
                    // Built outside the view call: a default written inside
                    // an interpolation reads, to the language audit, like an
                    // English literal cut off mid-hole.
                    let line = "\(r.kind ?? "—") · \(r.state ?? "—") · \(r.created_at ?? "")"
                    HStack {
                        Text(line)
                            .font(.caption2).foregroundStyle(Theme.t2)
                        Spacer()
                        Button(L10n.t("car.transcript", state.language)) {
                            readTranscript(r.id)
                        }
                        .font(.caption2).foregroundStyle(Theme.brandA)
                        .disabled(busy)
                    }
                }
                if let transcript {
                    let said = "\(transcript.kind ?? "") · \(transcript.note ?? "") · \(transcript.outcome ?? "")"
                    Text(said)
                        .font(.caption2).foregroundStyle(Theme.t3)
                }
            }.card()

            // The pairing card: the card's own words, straight from the wire.
            if let pair {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(Array(pair.how.enumerated()), id: \.offset) { _, line in
                        Text(line).font(.caption2.bold()).foregroundStyle(Theme.t2)
                    }
                    Text(pair.console_url)
                        .font(.caption2.monospaced()).foregroundStyle(Theme.txt)
                        .textSelection(.enabled)
                    Text(pair.note).font(.caption2).foregroundStyle(Theme.t3)
                    Text(L10n.t("qr.addr", state.language) + " "
                         + ApiClient.shared.pairQrUrl().absoluteString)
                        .font(.caption2.monospaced()).foregroundStyle(Theme.t3)
                        .textSelection(.enabled)
                }.card()
            }
        }
        .task { await load() }
    }

    private func load() async {
        pair = try? await ApiClient.shared.pairInfo()
        guard let token = state.token else { return }
        rows = (try? await ApiClient.shared.carrierBeacons(token: token)) ?? []
        rings = (try? await ApiClient.shared.rings(token: token)) ?? []
    }

    private func act(_ work: @escaping () async throws -> Void) {
        busy = true; error = nil
        Task {
            do { try await work(); await load() }
            catch { self.error = error.localizedDescription }
            busy = false
        }
    }

    private func place() {
        guard let token = state.token else { return }
        let name = label.trimmingCharacters(in: .whitespaces)
        act {
            _ = try await ApiClient.shared.placeCarrierBeacon(
                label: name, refKind: "object", disclose: disclose,
                token: token)
            label = ""
        }
    }

    private func chain(_ bid: String) {
        guard let token = state.token else { return }
        act { custody = try await ApiClient.shared.carrierCustody(
            bid: bid, token: token) }
    }

    private func sees(_ bid: String) {
        act { card = try await ApiClient.shared.scanCard(bid: bid) }
    }

    private func refresh(_ bid: String) {
        guard let token = state.token else { return }
        act { _ = try await ApiClient.shared.carrierBeacon(
            bid: bid, token: token) }
    }

    private func setState(_ bid: String, _ st: String) {
        guard let token = state.token else { return }
        act { _ = try await ApiClient.shared.setCarrierState(
            bid: bid, state: st, token: token) }
    }

    private func lift(_ bid: String) {
        guard let token = state.token else { return }
        act { _ = try await ApiClient.shared.liftCarrierBeacon(
            bid: bid, token: token) }
    }

    private func ring(_ bid: String) {
        act { _ = try await ApiClient.shared.ringHolder(bid: bid) }
    }

    private func found(_ bid: String) {
        act { _ = try await ApiClient.shared.reportFound(bid: bid) }
    }

    private func readTranscript(_ rid: String) {
        guard let token = state.token else { return }
        act { transcript = try await ApiClient.shared.ringTranscript(
            rid: rid, token: token) }
    }
}
