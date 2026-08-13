import SwiftUI

/// Admin: key management. Gated by the deployment's PDI_ADMIN_TOKEN — a
/// different credential from the tenant token, pasted here and kept only in
/// memory. Rotation re-seals every record immediately; retire deletes
/// non-active versions (safe only after a reseal).
struct AdminCard: View {
    @EnvironmentObject var state: AppState
    @State private var adminToken = ""
    @State private var info: KeysInfo?
    @State private var status: String?
    @State private var error: String?
    @State private var held: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(L10n.t("nadm.title", state.language)).font(.headline).foregroundStyle(Theme.txt)
            Text(L10n.t("nadm.req", state.language))
                .font(.caption).foregroundStyle(Theme.t2)
            SecureField(L10n.t("nadm.token", state.language), text: $adminToken)
                .foregroundStyle(Theme.txt)
                .padding(10).background(Theme.scrBot)
                .clipShape(RoundedRectangle(cornerRadius: 11))
                .overlay(RoundedRectangle(cornerRadius: 11).stroke(Theme.line, lineWidth: 1))

            HStack(spacing: 8) {
                Button(L10n.t("nadm.versions", state.language)) { load() }
                    .font(.caption.bold()).foregroundStyle(.white)
                    .padding(.horizontal, 12).padding(.vertical, 8)
                    .background(Theme.brandA).clipShape(Capsule())
                Button(L10n.t("nadm.rotate", state.language)) { rotate() }
                    .font(.caption.bold()).foregroundStyle(.white)
                    .padding(.horizontal, 12).padding(.vertical, 8)
                    .background(Theme.amber).clipShape(Capsule())
                    .disabled(info == nil)
                Button(L10n.t("nadm.retire", state.language)) { retire() }
                    .font(.caption.bold()).foregroundStyle(Theme.red)
                    .disabled(info == nil)
            }

            Button(L10n.t("nadm.dsr", state.language)) { exportAll() }
                .font(.caption.bold()).foregroundStyle(.white)
                .padding(.horizontal, 12).padding(.vertical, 8)
                .background(Theme.brand).clipShape(Capsule())

            if let held {
                Text(held).font(.caption).foregroundStyle(Theme.t2)
            }

            if let info {
                Text("provider: \(info.provider)")
                    .font(.caption2).foregroundStyle(Theme.t3)
                ForEach(info.versions) { v in
                    HStack {
                        Circle().fill(v.active ? Theme.green : Theme.t3)
                            .frame(width: 8, height: 8)
                        Text("v\(v.version)").font(.caption.bold())
                            .foregroundStyle(Theme.txt)
                        Text(v.active ? "active" : "inactive")
                            .font(.caption2)
                            .foregroundStyle(v.active ? Theme.green : Theme.t3)
                        Spacer()
                        Text(v.created_at ?? "").font(.caption2).foregroundStyle(Theme.t3)
                    }
                }
            }
            if let status { Text(status).font(.caption).foregroundStyle(Theme.green) }
            if let error { Text(error).font(.caption).foregroundStyle(Theme.red) }
        }.card()
    }

    private func load() {
        error = nil; status = nil
        Task {
            do { info = try await ApiClient.shared.adminKeys(adminToken: adminToken) }
            catch { self.error = error.localizedDescription }
        }
    }

    private func rotate() {
        error = nil; status = nil
        Task {
            do {
                info = try await ApiClient.shared.rotateKey(adminToken: adminToken)
                status = L10n.t("nadm.rotated", state.language)
            } catch { self.error = error.localizedDescription }
        }
    }

    private func retire() {
        error = nil; status = nil
        Task {
            do {
                let r = try await ApiClient.shared.retireKeys(adminToken: adminToken)
                info = KeysInfo(provider: info?.provider ?? "env", versions: r.versions)
                status = "Retired \(r.retired) old version(s)."
            } catch { self.error = error.localizedDescription }
        }
    }
}

extension AdminCard {
    /// The portability door. Counts and table names on the phone; the
    /// document itself is what the console downloads.
    func exportAll() {
        Task {
            do {
                let all = try await ApiClient.shared.exportEverything(
                    token: state.token ?? "")
                let rows = all.tables.values.reduce(0) { $0 + $1.count }
                held = "\(all.tables.count) table(s), \(rows) row(s) — \(all.note)"
            } catch {
                self.error = error.localizedDescription
            }
        }
    }
}

// MARK: tenants — the operator's half, on the phone

/// Create, restore, delete, mint, retention and the BAA — the console's
/// Custody admin block, behind the same PDI_ADMIN_TOKEN pasted into a field
/// and kept only in memory.
struct TenantsAdminCard: View {
    @EnvironmentObject var state: AppState
    @State private var adminToken = ""
    @State private var name = ""
    @State private var tid = ""
    @State private var retention = ""
    @State private var custName = ""
    @State private var opName = ""
    @State private var effDate = ""
    @State private var made: TenantMade?
    @State private var minted: String?
    @State private var baa: BaaOut?
    @State private var status: String?
    @State private var error: String?
    @State private var busy = false

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(L10n.t("tn.create", state.language))
                .font(.headline).foregroundStyle(Theme.txt)
            SecureField(L10n.t("nadm.token", state.language), text: $adminToken)
                .foregroundStyle(Theme.txt)
                .padding(10).background(Theme.scrBot)
                .clipShape(RoundedRectangle(cornerRadius: 11))
            HStack(spacing: 8) {
                TextField(L10n.t("co.name.ph", state.language), text: $name)
                    .foregroundStyle(Theme.txt)
                Button(L10n.t("tn.createbtn", state.language)) { create() }
                    .font(.caption.bold()).foregroundStyle(.white)
                    .padding(.horizontal, 12).padding(.vertical, 7)
                    .background(Theme.brandA).clipShape(Capsule())
                    .disabled(busy || name.trimmingCharacters(in: .whitespaces).isEmpty)
            }
            if let made {
                Text("\(made.id) · \(made.token)")
                    .font(.caption2.monospaced()).foregroundStyle(Theme.txt)
                    .textSelection(.enabled)
                Text(L10n.t("tn.token.note", state.language))
                    .font(.caption2).foregroundStyle(Theme.t2)
            }

            TextField(L10n.t("adm.tenant.ph", state.language), text: $tid)
                .foregroundStyle(Theme.txt)
            HStack(spacing: 10) {
                Button(L10n.t("cu.restore.all", state.language)) {
                    act { _ = try await ApiClient.shared.restoreTenant(
                        tid: tid, adminToken: adminToken) }
                }
                // Soft keeps the door open; hard is the one that cannot be
                // taken back. Both leave the audit chain standing.
                Button(L10n.t("cu.del.soft", state.language)) {
                    act { _ = try await ApiClient.shared.deleteTenant(
                        tid: tid, mode: "soft", adminToken: adminToken) }
                }
                Button(L10n.t("cu.del.hard", state.language)) {
                    act { _ = try await ApiClient.shared.deleteTenant(
                        tid: tid, mode: "hard", adminToken: adminToken) }
                }.foregroundStyle(Theme.red)
            }
            .font(.caption2).foregroundStyle(Theme.brandA)
            .disabled(busy || tid.isEmpty)
            HStack(spacing: 10) {
                Button(L10n.t("cu.mint.read", state.language)) { mint("read") }
                Button(L10n.t("cu.mint.write", state.language)) { mint("write") }
            }
            .font(.caption2).foregroundStyle(Theme.brandA)
            .disabled(busy || tid.isEmpty)
            if let minted {
                Text(minted)
                    .font(.caption2.monospaced()).foregroundStyle(Theme.txt)
                    .textSelection(.enabled)
                Text(L10n.t("cu.minted.note", state.language))
                    .font(.caption2).foregroundStyle(Theme.t2)
            }
            HStack(spacing: 8) {
                TextField(L10n.t("ky.retention", state.language), text: $retention)
                    .foregroundStyle(Theme.txt)
                Button(L10n.t("co.set", state.language)) {
                    act { _ = try await ApiClient.shared.setTenantRetention(
                        tid: tid, retention: retention, adminToken: adminToken) }
                }
                .font(.caption2).foregroundStyle(Theme.brandA)
                .disabled(busy || tid.isEmpty || retention.isEmpty)
            }

            // The paperwork a regulated tenant needs, on file or not.
            Text(L10n.t("cu.paperwork", state.language))
                .font(.subheadline.bold()).foregroundStyle(Theme.txt)
            TextField(L10n.t("cu.cust.name", state.language), text: $custName)
                .foregroundStyle(Theme.txt)
            TextField(L10n.t("cu.op.name", state.language), text: $opName)
                .foregroundStyle(Theme.txt)
            TextField(L10n.t("cu.eff", state.language), text: $effDate)
                .foregroundStyle(Theme.txt)
            HStack(spacing: 10) {
                Button(L10n.t("cu.record", state.language)) {
                    act { baa = try await ApiClient.shared.recordTenantBaa(
                        tid: tid, customer: custName, operatorName: opName,
                        date: effDate, adminToken: adminToken) }
                }
                Button(L10n.t("cu.onfile", state.language)) {
                    act { baa = try await ApiClient.shared.tenantBaa(
                        tid: tid, adminToken: adminToken) }
                }
                Button(L10n.t("cu.rescind", state.language)) {
                    act { _ = try await ApiClient.shared.rescindTenantBaa(
                        tid: tid, adminToken: adminToken)
                        baa = nil }
                }.foregroundStyle(Theme.red)
            }
            .font(.caption2).foregroundStyle(Theme.brandA)
            .disabled(busy || tid.isEmpty)
            if let baa, baa.executed {
                let line = "\(baa.customer_legal_name ?? "") ↔ \(baa.operator_legal_name ?? "") · \(baa.effective_date ?? "")"
                Text(line).font(.caption2).foregroundStyle(Theme.t2)
            }

            if let status { Text(status).font(.caption).foregroundStyle(Theme.green) }
            if let error { Text(error).font(.caption).foregroundStyle(Theme.red) }
        }.card()
    }

    private func act(_ work: @escaping () async throws -> Void) {
        busy = true; error = nil; status = nil
        Task {
            do { try await work(); status = "✓" }
            catch { self.error = error.localizedDescription }
            busy = false
        }
    }

    private func create() {
        act {
            made = try await ApiClient.shared.createTenant(
                name: name.trimmingCharacters(in: .whitespaces),
                adminToken: adminToken)
            name = ""
        }
    }

    private func mint(_ role: String) {
        act {
            minted = try await ApiClient.shared.mintTenantToken(
                tid: tid, role: role, adminToken: adminToken).token
        }
    }
}

// MARK: the agent at the gate

/// What the agent may do and may never do, who is on shift, and what it
/// sent when nobody was — the console's Continuity gate block, with the
/// tenant's own token.
struct GateCard: View {
    @EnvironmentObject var state: AppState
    @State private var ceiling: GateCeilingOut?
    @State private var channel: GateChannelOut?
    @State private var roster: GateRosterOut?
    @State private var pages: [GatePageOut] = []
    @State private var rosterName = ""
    @State private var rosterRole = ""
    @State private var tz = ""
    @State private var error: String?
    @State private var busy = false

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(L10n.t("co.ceiling", state.language))
                .font(.headline).foregroundStyle(Theme.txt)
            if let ceiling {
                Text(ceiling.rule).font(.caption2).foregroundStyle(Theme.t2)
                Text(L10n.t("co.may", state.language) + " "
                     + ceiling.may.keys.sorted().joined(separator: ", "))
                    .font(.caption2).foregroundStyle(Theme.t2)
                Text(L10n.t("co.maynever", state.language) + " "
                     + ceiling.may_never.keys.sorted().joined(separator: ", "))
                    .font(.caption2).foregroundStyle(Theme.t2)
            }
            if let channel {
                Text(L10n.t("co.channel", state.language) + " "
                     + L10n.t(channel.configured ? "co.configured"
                                                 : "co.notconfigured",
                              state.language)
                     + (channel.signed == true
                        ? " " + L10n.t("co.signed", state.language) : ""))
                    .font(.caption2).foregroundStyle(Theme.t2)
            }

            Text(L10n.t("co.shift", state.language))
                .font(.subheadline.bold()).foregroundStyle(Theme.txt)
            if let roster {
                if roster.roster.isEmpty {
                    Text(L10n.t("co.noroster", state.language))
                        .font(.caption2).foregroundStyle(Theme.t2)
                }
                if !roster.anybody_on_shift {
                    Text(L10n.t("co.nobody", state.language))
                        .font(.caption2).foregroundStyle(Theme.t2)
                }
                ForEach(roster.roster, id: \.id) { entry in
                    HStack {
                        Text("\(entry.name) · \(entry.role)")
                            .font(.caption2).foregroundStyle(Theme.t2)
                        Spacer()
                        Button(L10n.t("co.remove", state.language)) {
                            act { _ = try await ApiClient.shared.removeFromRoster(
                                rid: entry.id, token: state.token ?? "") }
                        }
                        .font(.caption2).foregroundStyle(Theme.red)
                        .disabled(busy)
                    }
                }
            }
            HStack(spacing: 8) {
                TextField(L10n.t("co.name.ph", state.language), text: $rosterName)
                    .foregroundStyle(Theme.txt)
                TextField(L10n.t("co.role.ph", state.language), text: $rosterRole)
                    .foregroundStyle(Theme.txt)
                Button(L10n.t("co.addroster", state.language)) {
                    act {
                        _ = try await ApiClient.shared.addToRoster(
                            name: rosterName, role: rosterRole,
                            token: state.token ?? "")
                        rosterName = ""
                    }
                }
                .font(.caption2).foregroundStyle(Theme.brandA)
                .disabled(busy || rosterName.isEmpty)
            }
            HStack(spacing: 8) {
                TextField(L10n.t("co.tz.ph", state.language), text: $tz)
                    .foregroundStyle(Theme.txt)
                Button(L10n.t("co.set", state.language)) {
                    act { _ = try await ApiClient.shared.setGateTimezone(
                        tz, token: state.token ?? "")
                        tz = "" }
                }
                .font(.caption2).foregroundStyle(Theme.brandA)
                .disabled(busy || tz.isEmpty)
            }

            Text(L10n.t("co.sent", state.language))
                .font(.subheadline.bold()).foregroundStyle(Theme.txt)
            Text(L10n.t("co.sent.note", state.language))
                .font(.caption2).foregroundStyle(Theme.t2)
            if pages.isEmpty {
                Text(L10n.t("co.nothingpaged", state.language))
                    .font(.caption2).foregroundStyle(Theme.t2)
            }
            ForEach(Array(pages.enumerated()), id: \.offset) { _, page in
                HStack {
                    // `state` is the wire's word — "sent" is the good end.
                    let line = "\(page.id ?? "—") · \(page.state ?? "—")"
                    Text(line).font(.caption2).foregroundStyle(Theme.t2)
                    Spacer()
                    if page.state != "sent", let pid = page.id {
                        Button(L10n.t("co.retry", state.language)) {
                            act { _ = try await ApiClient.shared.retryGatePage(
                                pid: pid, token: state.token ?? "") }
                        }
                        .font(.caption2).foregroundStyle(Theme.brandA)
                        .disabled(busy)
                    }
                }
            }
            if let error { Text(error).font(.caption).foregroundStyle(Theme.red) }
        }
        .card()
        .task { await load() }
    }

    private func load() async {
        guard let token = state.token else { return }
        ceiling = try? await ApiClient.shared.gateCeiling(token: token)
        channel = try? await ApiClient.shared.gateChannel(token: token)
        roster = try? await ApiClient.shared.gateRoster(token: token)
        pages = (try? await ApiClient.shared.gatePages(token: token)) ?? []
    }

    private func act(_ work: @escaping () async throws -> Void) {
        busy = true; error = nil
        Task {
            do { try await work(); await load() }
            catch { self.error = error.localizedDescription }
            busy = false
        }
    }
}

// MARK: continuity — what outlives the tenant, on the phone

/// Bequests through their whole life — recorded, activated by the executor,
/// taken back, redeemed by the heir — plus contributions, the snapshot pair,
/// and the retention ops. The console's Continuity and custody blocks.
struct ContinuityCard: View {
    @EnvironmentObject var state: AppState
    @State private var rows: [BequestOut] = []
    @State private var grantee = ""
    @State private var prefixes = ""
    @State private var note = ""
    @State private var adminToken = ""
    @State private var ref = ""
    @State private var mintedGrant: String?
    @State private var grantToken = ""
    @State private var custKey = ""
    @State private var heirKeys: [String] = []
    @State private var readBack: String?
    @State private var contribSource = ""
    @State private var contribRef = ""
    @State private var contribLine: String?
    @State private var snapCount: Int?
    @State private var sweepLine: String?
    @State private var status: String?
    @State private var error: String?
    @State private var busy = false

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(L10n.t("co.bequests", state.language))
                .font(.headline).foregroundStyle(Theme.txt)
            Text(L10n.t("co.bequests.note", state.language))
                .font(.caption2).foregroundStyle(Theme.t2)
            if rows.isEmpty {
                Text(L10n.t("co.nothing", state.language))
                    .font(.caption2).foregroundStyle(Theme.t2)
            }
            ForEach(rows, id: \.id) { b in
                VStack(alignment: .leading, spacing: 3) {
                    HStack {
                        Text(b.grantee_name)
                            .font(.caption.bold()).foregroundStyle(Theme.txt)
                        Text(L10n.t(b.revoked ? "co.revoke"
                                    : b.activated ? "co.inforce" : "co.dormant",
                                    state.language))
                            .font(.caption2).foregroundStyle(Theme.t2)
                        Spacer()
                        if !b.revoked {
                            Button(L10n.t("co.revoke", state.language)) {
                                act { _ = try await ApiClient.shared.revokeBequest(
                                    bid: b.id, token: state.token ?? "") }
                            }
                            .font(.caption2).foregroundStyle(Theme.red)
                            .disabled(busy)
                        }
                    }
                    Text(L10n.t("co.wouldopen", state.language) + " "
                         + b.key_prefixes.joined(separator: ", "))
                        .font(.caption2).foregroundStyle(Theme.t2)
                    // The executor's press, one per dormant row; the taking
                    // back, one per row in force.
                    if !b.activated && !b.revoked {
                        Button(L10n.t("co.activate", state.language)) {
                            act {
                                let out = try await ApiClient.shared.activateBequest(
                                    bid: b.id, ref: ref, adminToken: adminToken)
                                mintedGrant = out.grant_token
                            }
                        }
                        .font(.caption2).foregroundStyle(Theme.brandA)
                        .disabled(busy || adminToken.isEmpty || ref.isEmpty)
                    }
                    if b.activated && !b.revoked {
                        Button(L10n.t("co.revoke.grant", state.language)) {
                            act { _ = try await ApiClient.shared.revokeBequestGrant(
                                bid: b.id, adminToken: adminToken) }
                        }
                        .font(.caption2).foregroundStyle(Theme.red)
                        .disabled(busy || adminToken.isEmpty)
                    }
                }
            }
            TextField(L10n.t("co.grantee.ph", state.language), text: $grantee)
                .foregroundStyle(Theme.txt)
            TextField(L10n.t("co.prefixes.ph", state.language), text: $prefixes)
                .foregroundStyle(Theme.txt)
            TextField(L10n.t("co.note.ph", state.language), text: $note)
                .foregroundStyle(Theme.txt)
            Button(L10n.t("co.record", state.language)) { record() }
                .font(.caption.bold()).foregroundStyle(.white)
                .padding(.horizontal, 12).padding(.vertical, 7)
                .background(Theme.brandA).clipShape(Capsule())
                .disabled(busy || grantee.isEmpty || prefixes.isEmpty)

            Text(L10n.t("co.activation", state.language))
                .font(.subheadline.bold()).foregroundStyle(Theme.txt)
            Text(L10n.t("co.activation.note", state.language))
                .font(.caption2).foregroundStyle(Theme.t2)
            SecureField(L10n.t("co.admin.ph", state.language), text: $adminToken)
                .foregroundStyle(Theme.txt)
            TextField(L10n.t("co.ref.ph", state.language), text: $ref)
                .foregroundStyle(Theme.txt)
            if let mintedGrant {
                Text(L10n.t("co.minted", state.language) + " "
                     + L10n.t("co.minted.note", state.language))
                    .font(.caption2).foregroundStyle(Theme.t2)
                Text(mintedGrant)
                    .font(.caption2.monospaced()).foregroundStyle(Theme.txt)
                    .textSelection(.enabled)
            }

            // The heir's side: two separate secrets, and one without the
            // other opens nothing.
            Text(L10n.t("co.redeem", state.language))
                .font(.subheadline.bold()).foregroundStyle(Theme.txt)
            Text(L10n.t("co.redeem.note", state.language))
                .font(.caption2).foregroundStyle(Theme.t2)
            TextField(L10n.t("co.grant.ph", state.language), text: $grantToken)
                .foregroundStyle(Theme.txt)
            SecureField(L10n.t("co.custkey.ph", state.language), text: $custKey)
                .foregroundStyle(Theme.txt)
            HStack(spacing: 10) {
                Button(L10n.t("co.whatopen", state.language)) {
                    act { heirKeys = try await ApiClient.shared.bequestKeys(
                        grantToken: grantToken, customerKey: custKey).keys }
                }
                Button(L10n.t("co.read", state.language)) {
                    act {
                        guard let first = heirKeys.first else { return }
                        let data = try await ApiClient.shared.bequestRead(
                            key: first, grantToken: grantToken,
                            customerKey: custKey)
                        readBack = String(data: data, encoding: .utf8)
                    }
                }.disabled(heirKeys.isEmpty)
            }
            .font(.caption2).foregroundStyle(Theme.brandA)
            .disabled(busy || grantToken.isEmpty || custKey.isEmpty)
            if !heirKeys.isEmpty {
                Text(heirKeys.joined(separator: ", "))
                    .font(.caption2.monospaced()).foregroundStyle(Theme.t2)
            }
            if let readBack {
                Text(readBack).font(.caption2.monospaced())
                    .foregroundStyle(Theme.t2).lineLimit(4)
            }

            // Contributions: what the tandem products sealed in, by count
            // and key only.
            Text(L10n.t("bri.contribute", state.language))
                .font(.subheadline.bold()).foregroundStyle(Theme.txt)
            if let contribLine {
                Text(contribLine).font(.caption2).foregroundStyle(Theme.t2)
            }
            TextField(L10n.t("bri.source.ph", state.language), text: $contribSource)
                .foregroundStyle(Theme.txt)
            TextField(L10n.t("bri.ref.ph", state.language), text: $contribRef)
                .foregroundStyle(Theme.txt)
            HStack(spacing: 10) {
                Button(L10n.t("bri.contribute", state.language)) { contribute() }
                    .disabled(busy || contribSource.isEmpty)
                Button(L10n.t("bri.withdraw", state.language)) {
                    act { _ = try await ApiClient.shared.withdrawContribution(
                        ref: contribRef, token: state.token ?? "") }
                }.disabled(busy || contribRef.isEmpty)
            }
            .font(.caption2).foregroundStyle(Theme.brandA)

            // The custody ops: the whole tenant in hand and back, the
            // retention window, the sweep, and the demo seed.
            HStack(spacing: 10) {
                Button(L10n.t("cu.snapshot", state.language)) {
                    act { snapCount = try await ApiClient.shared.snapshotRecords(
                        token: state.token ?? "") }
                }
                Button(L10n.t("cu.restore", state.language)) {
                    act { _ = try await ApiClient.shared.restoreSnapshot(
                        token: state.token ?? "") }
                }.disabled(snapCount == nil)
                Button(L10n.t("ky.window", state.language)) {
                    act {
                        let r = try await ApiClient.shared.retentionPolicy(
                            adminToken: adminToken)
                        sweepLine = r.recovery_window
                    }
                }.disabled(adminToken.isEmpty)
                Button(L10n.t("ky.sweep", state.language)) {
                    act {
                        let s = try await ApiClient.shared.retentionSweep(
                            adminToken: adminToken)
                        sweepLine = "\(s.purged_tenants) · \(s.expired_records) · \(s.recovery_window)"
                    }
                }.disabled(adminToken.isEmpty)
                Button(L10n.t("bri.seed", state.language)) {
                    act { _ = try await ApiClient.shared.seedDemo(
                        adminToken: adminToken)
                        status = L10n.t("bri.seeded", state.language) }
                }.disabled(adminToken.isEmpty)
            }
            .font(.caption2).foregroundStyle(Theme.brandA)
            .disabled(busy)
            if let snapCount {
                Text("\(snapCount)").font(.caption2).foregroundStyle(Theme.t2)
            }
            if let sweepLine {
                Text(sweepLine).font(.caption2).foregroundStyle(Theme.t2)
            }

            if let status { Text(status).font(.caption).foregroundStyle(Theme.green) }
            if let error { Text(error).font(.caption).foregroundStyle(Theme.red) }
        }
        .card()
        .task { await load() }
    }

    private func load() async {
        guard let token = state.token else { return }
        rows = (try? await ApiClient.shared.bequests(token: token)) ?? []
        if let c = try? await ApiClient.shared.contributions(token: token) {
            contribLine = L10n.t("bri.held", state.language)
                .replacingOccurrences(of: "{n}", with: String(c.count))
        }
    }

    private func act(_ work: @escaping () async throws -> Void) {
        busy = true; error = nil; status = nil
        Task {
            do { try await work(); await load() }
            catch { self.error = error.localizedDescription }
            busy = false
        }
    }

    private func record() {
        let parts = prefixes.split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
        act {
            _ = try await ApiClient.shared.createBequest(
                grantee: grantee, prefixes: parts,
                note: note.isEmpty ? nil : note, token: state.token ?? "")
            grantee = ""; prefixes = ""; note = ""
        }
    }

    private func contribute() {
        act {
            let c = try await ApiClient.shared.contribute(
                source: contribSource,
                ref: contribRef.isEmpty ? nil : contribRef,
                token: state.token ?? "")
            status = L10n.t("bri.sealed", state.language)
                .replacingOccurrences(of: "{key}", with: c.key)
            contribSource = ""
        }
    }
}

// MARK: posture — where the vault lives, and whether it is up

/// The deployment's own account of itself: health, the hosting mode it is
/// in and could move to, what went out through operations, the audit
/// vocabulary, and whether the paperwork is on file.
struct PostureCard: View {
    @EnvironmentObject var state: AppState
    @State private var healthLine: String?
    @State private var modes: [(id: String, label: String)] = []
    @State private var mine: HostingModeOut?
    @State private var historyCount: Int?
    @State private var tid = ""
    @State private var opsLine: String?
    @State private var schemaLine: String?
    @State private var baaLine: String?
    @State private var status: String?
    @State private var error: String?
    @State private var busy = false

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(L10n.t("ov.health", state.language))
                .font(.headline).foregroundStyle(Theme.txt)
            if let healthLine {
                Text(healthLine).font(.caption2).foregroundStyle(Theme.t2)
            }

            Text(L10n.t("cu.where", state.language))
                .font(.subheadline.bold()).foregroundStyle(Theme.txt)
            TextField(L10n.t("adm.tenant.ph", state.language), text: $tid)
                .foregroundStyle(Theme.txt)
            HStack(spacing: 8) {
                Button(L10n.t("cu.where", state.language)) { readMine() }
                Button(L10n.t("cu.deploy", state.language)) {
                    act { _ = try await ApiClient.shared.recordDeployment(
                        token: state.token ?? "") }
                }
            }
            .font(.caption2).foregroundStyle(Theme.brandA)
            .disabled(busy)
            if let mine {
                Text("\(mine.title) — \(mine.means) · \(mine.price)")
                    .font(.caption2).foregroundStyle(Theme.t2)
                if let why = mine.free_because {
                    Text(L10n.t("cu.free", state.language) + " " + why)
                        .font(.caption2).foregroundStyle(Theme.t2)
                }
                Text(L10n.t("cu.we", state.language) + " "
                     + mine.we_are_responsible_for.joined(separator: ", "))
                    .font(.caption2).foregroundStyle(Theme.t2)
                Text(L10n.t("cu.you", state.language) + " "
                     + mine.you_are_responsible_for.joined(separator: ", "))
                    .font(.caption2).foregroundStyle(Theme.t2)
            }
            if let historyCount {
                Text("\(historyCount)").font(.caption2).foregroundStyle(Theme.t2)
            }
            // Moving is one press per mode the deployment offers, priced on
            // the button the way the console prices it.
            ForEach(modes, id: \.id) { mode in
                Button(mode.label) {
                    act { _ = try await ApiClient.shared.setHosting(
                        tid: tid, mode: mode.id, token: state.token ?? "") }
                }
                .font(.caption2).foregroundStyle(Theme.brandA)
                .disabled(busy || tid.isEmpty)
            }

            Text(L10n.t("op.title", state.language))
                .font(.subheadline.bold()).foregroundStyle(Theme.txt)
            if let opsLine {
                Text(opsLine).font(.caption2).foregroundStyle(Theme.t2)
            }
            if let schemaLine {
                Text(L10n.t("au.actions", state.language) + " " + schemaLine)
                    .font(.caption2).foregroundStyle(Theme.t2)
            }
            HStack(spacing: 8) {
                Button(L10n.t("cu.onfile", state.language)) {
                    act {
                        let baa = try await ApiClient.shared.baaStatus(
                            token: state.token ?? "")
                        baaLine = baa.executed
                            ? (baa.effective_date ?? "✓")
                            : (baa.note ?? L10n.t("cu.no", state.language))
                    }
                }
            }
            .font(.caption2).foregroundStyle(Theme.brandA)
            .disabled(busy)
            if let baaLine {
                Text(baaLine).font(.caption2).foregroundStyle(Theme.t2)
            }

            if let status { Text(status).font(.caption).foregroundStyle(Theme.green) }
            if let error { Text(error).font(.caption).foregroundStyle(Theme.red) }
        }
        .card()
        .task { await load() }
    }

    private func load() async {
        if let h = try? await ApiClient.shared.health() {
            healthLine = h.status
        }
        modes = (try? await ApiClient.shared.hostingModes()) ?? []
        if let s = try? await ApiClient.shared.auditSchema() {
            schemaLine = "\(s.actions.count) · \(s.retention)"
        }
        guard let token = state.token else { return }
        if let ops = try? await ApiClient.shared.operations(token: token) {
            opsLine = ops.entries.isEmpty
                ? L10n.t("op.none", state.language)
                : L10n.t("op.events", state.language) + " \(ops.entries.count)"
        }
    }

    private func readMine() {
        guard let token = state.token, !tid.isEmpty else { return }
        act {
            mine = try await ApiClient.shared.hosting(tid: tid, token: token)
            historyCount = try await ApiClient.shared.hostingHistory(
                tid: tid, token: token).history.count
        }
    }

    private func act(_ work: @escaping () async throws -> Void) {
        busy = true; error = nil; status = nil
        Task {
            do { try await work() }
            catch { self.error = error.localizedDescription }
            busy = false
        }
    }
}

// MARK: positions — the assistant builder, on the phone

/// A position built from two answers, listed, and opened — the console's
/// whole intake is optional by design, so the smallest honest intake is an
/// industry and a job title.
struct PositionsCard: View {
    @EnvironmentObject var state: AppState
    @State private var industry = ""
    @State private var jobTitle = ""
    @State private var line: String?
    @State private var savedLine: String?
    @State private var firstId: String?
    @State private var error: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(L10n.t("pos.build", state.language))
                .font(.headline).foregroundStyle(Theme.txt)
            TextField(L10n.t("pos.industry", state.language), text: $industry)
                .foregroundStyle(Theme.txt)
            TextField(L10n.t("pos.jobtitle", state.language), text: $jobTitle)
                .foregroundStyle(Theme.txt)
            HStack(spacing: 10) {
                Button(L10n.t("pos.build", state.language)) { build() }
                    .disabled(industry.isEmpty)
                Button(L10n.t("pos.open", state.language)) { openFirst() }
                    .disabled(firstId == nil)
            }
            .font(.caption2).foregroundStyle(Theme.brandA)
            if let line {
                Text(L10n.t("pos.blueprint", state.language) + " " + line)
                    .font(.caption2).foregroundStyle(Theme.t2)
            }
            if let savedLine {
                Text(savedLine).font(.caption2).foregroundStyle(Theme.t2)
            }
            if let error { Text(error).font(.caption).foregroundStyle(Theme.red) }
        }
        .card()
        .task { await list() }
    }

    private func list() async {
        guard let token = state.token else { return }
        if let saved = try? await ApiClient.shared.listPositions(token: token) {
            savedLine = saved.count == 0
                ? L10n.t("pos.none", state.language)
                : L10n.t("pos.saved", state.language) + " \(saved.count)"
            firstId = saved.ids.first
        }
    }

    private func build() {
        Task {
            do {
                let b = try await ApiClient.shared.buildPosition(
                    industry: industry, jobTitle: jobTitle,
                    token: state.token ?? "")
                line = "\(b.id) · \(b.industry)"
                await list()
            } catch { self.error = error.localizedDescription }
        }
    }

    private func openFirst() {
        guard let firstId else { return }
        Task {
            if let b = try? await ApiClient.shared.getPosition(
                id: firstId, token: state.token ?? "") {
                line = "\(b.id) · \(b.industry)"
            }
        }
    }
}
