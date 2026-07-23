import SwiftUI

/// Robots as vault-backed data sources: bind a platform, seal what it collects
/// (maps, snapshots, sensor logs) into the vault, and see its sealed keys.
struct RobotsView: View {
    @EnvironmentObject var state: AppState
    @State private var catalog: [RobotSpec] = []
    @State private var chosen = "saros_20"
    @State private var robots: [Robot] = []
    @State private var lastKey: String?
    @State private var keysByRobot: [String: Int] = [:]
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Robots").font(.title2.bold()).foregroundStyle(Theme.txt)
                Text("What your robots see stays sealed — every intake is encrypted at rest and hash-chained in the audit log.")
                    .font(.footnote).foregroundStyle(Theme.t2)

                VStack(alignment: .leading, spacing: 10) {
                    Text("Bind a robot").font(.headline).foregroundStyle(Theme.txt)
                    Picker("", selection: $chosen) {
                        ForEach(catalog, id: \.model) {
                            Text("\($0.label) · \($0.maker)").tag($0.model)
                        }
                    }.pickerStyle(.menu).tint(Theme.brandA)
                    Button(action: bind) {
                        HStack { if busy { ProgressView().tint(.white) }; Text("Bind").bold() }
                            .frame(maxWidth: .infinity).padding(.vertical, 12)
                            .background(Theme.brand).foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                    }.disabled(busy || catalog.isEmpty)
                }.card()

                if let error { Text(error).font(.footnote).foregroundStyle(Theme.red) }

                ForEach(robots, id: \.id) { r in
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(r.name).font(.subheadline.bold()).foregroundStyle(Theme.txt)
                            Spacer()
                            Text("\(keysByRobot[r.id] ?? r.collected ?? 0) sealed")
                                .font(.caption).foregroundStyle(Theme.green)
                        }
                        HStack(spacing: 8) {
                            sealButton("Seal map", r, "map", "{\"rooms\": 5}")
                            sealButton("Snapshot", r, "snapshot", "camera still")
                            sealButton("Sensor log", r, "sensor_log", "steps & doors")
                        }
                    }.card()
                }

                if let lastKey {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Sealed").font(.headline).foregroundStyle(Theme.txt)
                        Text(lastKey).font(.system(.caption, design: .monospaced))
                            .foregroundStyle(Theme.t2)
                        Text("Read it (audited) via Vault → the key above.")
                            .font(.caption).foregroundStyle(Theme.t3)
                    }.card()
                }
            }.padding(20)
        }
        .task { await load() }
    }

    private func sealButton(_ label: String, _ robot: Robot, _ kind: String,
                            _ content: String) -> some View {
        Button(label) { seal(robot, kind, content) }
            .font(.caption.bold()).foregroundStyle(.white)
            .padding(.horizontal, 10).padding(.vertical, 7)
            .background(Theme.brandA).clipShape(Capsule())
    }

    private func load() async {
        guard let token = state.token else { return }
        catalog = (try? await ApiClient.shared.roboticsCatalog(token: token))?.robots ?? []
        robots = (try? await ApiClient.shared.robots(token: token)) ?? []
        for r in robots {
            if let d = try? await ApiClient.shared.robotData(token: token, rid: r.id) {
                keysByRobot[r.id] = d.keys.count
            }
        }
    }

    private func bind() {
        guard let token = state.token else { return }
        busy = true; error = nil
        Task {
            do { _ = try await ApiClient.shared.bindRobot(token: token, model: chosen) }
            catch { self.error = error.localizedDescription }
            await load(); busy = false
        }
    }

    private func seal(_ robot: Robot, _ kind: String, _ content: String) {
        guard let token = state.token else { return }
        error = nil
        Task {
            do {
                let r = try await ApiClient.shared.ingest(
                    token: token, rid: robot.id, kind: kind, content: content)
                lastKey = r.key
            } catch { self.error = error.localizedDescription }
            await load()
        }
    }
}
