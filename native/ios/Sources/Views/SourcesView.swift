import SwiftUI

/// Sources: everything that feeds the vault — robot bodies and social-platform
/// connectors — behind one tab so the bar stays tidy.
struct SourcesView: View {
    enum Tab: String, CaseIterable { case robots = "Robots", connectors = "Connectors" }
    @State private var tab: Tab = .robots

    var body: some View {
        VStack(spacing: 0) {
            Picker("", selection: $tab) {
                ForEach(Tab.allCases, id: \.self) { Text($0.rawValue).tag($0) }
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, 20).padding(.top, 8)

            switch tab {
            case .robots: RobotsView()
            case .connectors: ConnectorsSection()
            }
        }
    }
}

/// Social-platform connectors: link an account to collect (sealed into the
/// vault) or publish; every ingest is audited like any vault write.
private struct ConnectorsSection: View {
    @State private var platform = "instagram"
    @State private var handle = ""
    @State private var conns: [SocialConn] = []
    @State private var status: String?
    @State private var error: String?
    @EnvironmentObject var state: AppState

    private let platforms = ["instagram", "x", "tiktok", "facebook", "linkedin",
                             "youtube", "whatsapp", "discord", "twitch",
                             "pinterest", "snapchat", "mastodon"]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Connectors").font(.title2.bold()).foregroundStyle(Theme.txt)
                Text("Link a platform account. Collected content is sealed into the vault; every ingest is hash-chained in the audit log.")
                    .font(.footnote).foregroundStyle(Theme.t2)

                VStack(alignment: .leading, spacing: 10) {
                    Picker("", selection: $platform) {
                        ForEach(platforms, id: \.self) { Text($0.capitalized).tag($0) }
                    }.pickerStyle(.menu).tint(Theme.brandA)
                    TextField("handle (optional)", text: $handle)
                        .foregroundStyle(Theme.txt).textInputAutocapitalization(.never)
                        .padding(10).background(Theme.scrBot)
                        .clipShape(RoundedRectangle(cornerRadius: 11))
                        .overlay(RoundedRectangle(cornerRadius: 11).stroke(Theme.line, lineWidth: 1))
                    HStack(spacing: 8) {
                        connectButton("Connect to collect", "collect")
                        connectButton("Connect to publish", "publish")
                    }
                }.card()

                if let error { Text(error).font(.footnote).foregroundStyle(Theme.red) }
                if let status { Text(status).font(.caption).foregroundStyle(Theme.green) }

                ForEach(conns, id: \.id) { c in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text(c.platform.capitalized).font(.subheadline.bold())
                                .foregroundStyle(Theme.txt)
                            Text(c.direction).font(.caption).foregroundStyle(Theme.t2)
                            Spacer()
                            if let h = c.handle { Text("@\(h)").font(.caption).foregroundStyle(Theme.t3) }
                        }
                        HStack(spacing: 8) {
                            if c.direction == "collect" {
                                smallButton("Ingest sample") { ingest(c) }
                            } else {
                                smallButton("Publish update") { publish(c) }
                            }
                            Button("Disconnect") { revoke(c) }
                                .font(.caption).foregroundStyle(Theme.red)
                        }
                    }.card()
                }
            }.padding(20)
        }
        .task { await load() }
    }

    private func connectButton(_ label: String, _ direction: String) -> some View {
        Button(label) { connect(direction) }
            .font(.caption.bold()).foregroundStyle(.white)
            .frame(maxWidth: .infinity).padding(.vertical, 10)
            .background(Theme.brandA).clipShape(RoundedRectangle(cornerRadius: 11))
    }

    private func smallButton(_ label: String, _ action: @escaping () -> Void) -> some View {
        Button(label, action: action)
            .font(.caption.bold()).foregroundStyle(.white)
            .padding(.horizontal, 12).padding(.vertical, 7)
            .background(Theme.brandA).clipShape(Capsule())
    }

    private func load() async {
        guard let token = state.token else { return }
        conns = (try? await ApiClient.shared.connectors(token: token)) ?? []
    }

    private func connect(_ direction: String) {
        guard let token = state.token else { return }
        error = nil; status = nil
        Task {
            do {
                _ = try await ApiClient.shared.createConnector(
                    token: token, platform: platform, direction: direction,
                    handle: handle)
                handle = ""
            } catch { self.error = error.localizedDescription }
            await load()
        }
    }

    private func ingest(_ c: SocialConn) {
        guard let token = state.token else { return }
        Task {
            do {
                try await ApiClient.shared.connectorIngest(
                    token: token, cid: c.id, content: "sample post from \(c.platform)")
                status = "sealed one item from \(c.platform)"
            } catch { self.error = error.localizedDescription }
        }
    }

    private func publish(_ c: SocialConn) {
        guard let token = state.token else { return }
        Task {
            do {
                try await ApiClient.shared.connectorPublish(
                    token: token, cid: c.id, content: "An update from the vault.")
                status = "published to \(c.platform)"
            } catch { self.error = error.localizedDescription }
        }
    }

    private func revoke(_ c: SocialConn) {
        guard let token = state.token else { return }
        Task {
            try? await ApiClient.shared.revokeConnector(token: token, cid: c.id)
            await load()
        }
    }
}
