import SwiftUI

/// The resident intelligence: the agent living in the vault process.
///
/// The same engine a colocation or own-facility deployment runs beside its
/// data, reached here over the standard service — one engine, one privacy
/// posture, whichever hosting a tenant chose. The screen repeats the two
/// honesty rules rather than smoothing them over: `leaves_host` renders
/// beside every tool and step, and the posture names the embedder and
/// whether a local model is present — the stub never answers under a
/// model's name.
struct ResidentView: View {
    @EnvironmentObject var state: AppState
    @State private var posture: ResidentPosture?
    @State private var tasks: [ResidentTask] = []
    @State private var datasets: [ResidentDataset] = []
    @State private var rows: [String] = []
    @State private var rowsOf = ""
    @State private var goal = ""
    @State private var embedKey = ""
    @State private var embedText = ""
    @State private var query = ""
    @State private var matches: [ResidentMatch] = []
    @State private var status: String?
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(L10n.t("res.title", state.language))
                    .font(.title2.bold())
                if let posture {
                    // The server's own sentences, verbatim: what runs here
                    // and what the privacy posture is are its claims to make.
                    Text(posture.means).font(.footnote)
                        .foregroundStyle(.secondary)
                    // Concatenation rather than interpolation: the
                    // untranslated-literal scanner reads a key nested inside
                    // an interpolated segment as prose on the screen.
                    Text(L10n.t("res.hosting", state.language) + ": "
                         + posture.hosting_mode + " · "
                         + L10n.t("res.model", state.language) + ": "
                         + (posture.local_model
                            ?? L10n.t("res.nomodel", state.language))
                         + " · " + posture.embedder)
                        .font(.caption)
                    ForEach(posture.tools, id: \.name) { tool in
                        Text(tool.name + " — " + tool.means + " · "
                             + (tool.leaves_host
                                ? L10n.t("res.leaves", state.language)
                                : L10n.t("res.stays", state.language)))
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                    Text(posture.privacy).font(.caption2)
                        .foregroundStyle(.secondary)
                }

                Text(L10n.t("res.plan", state.language)).font(.headline)
                TextField(L10n.t("res.plan.ph", state.language), text: $goal)
                    .textFieldStyle(.roundedBorder)
                Button(L10n.t("res.plan.go", state.language)) {
                    Task {
                        await run {
                            _ = try await ApiClient.shared.residentPlan(
                                goal: goal, token: state.token ?? "")
                            goal = ""
                        }
                    }
                }.disabled(goal.trimmingCharacters(in: .whitespaces).isEmpty)

                Text(L10n.t("res.tasks", state.language)).font(.headline)
                ForEach(tasks, id: \.id) { task in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(task.goal + " — " + task.status).font(.callout)
                        ForEach(task.plan_steps, id: \.position) { step in
                            Text(String(step.position) + ". " + step.tool
                                 + " — " + step.status
                                 + (step.leaves_host
                                    ? " · " + L10n.t("res.leaves",
                                                     state.language) : "")
                                 + (step.summary.map { " · " + $0 } ?? "")
                                 + (step.error.map { " · " + $0 } ?? ""))
                                .font(.caption2)
                                .foregroundStyle(step.error == nil
                                                 ? .secondary : Color.red)
                        }
                        if task.status == "planned" || task.status == "failed" {
                            Button(L10n.t("res.run", state.language)) {
                                Task {
                                    await run {
                                        _ = try await ApiClient.shared.residentRun(
                                            tid: task.id, token: state.token ?? "")
                                    }
                                }
                            }.font(.caption)
                        }
                    }
                }

                Text(L10n.t("res.datasets", state.language)).font(.headline)
                ForEach(datasets, id: \.dataset) { d in
                    Button(d.dataset + " · " + String(d.row_count)) {
                        Task {
                            await run {
                                rows = try await ApiClient.shared.residentRows(
                                    name: d.dataset, token: state.token ?? "")
                                rowsOf = d.dataset
                            }
                        }
                    }.font(.caption)
                }
                if !rows.isEmpty {
                    Text(rowsOf).font(.caption.bold())
                    ForEach(rows, id: \.self) { row in
                        Text(row).font(.caption2.monospaced())
                            .foregroundStyle(.secondary)
                    }
                }

                Text(L10n.t("res.embed", state.language)).font(.headline)
                TextField(L10n.t("res.embed.key", state.language),
                          text: $embedKey)
                    .textFieldStyle(.roundedBorder)
                TextField(L10n.t("res.embed.text", state.language),
                          text: $embedText)
                    .textFieldStyle(.roundedBorder)
                Button(L10n.t("res.embed.go", state.language)) {
                    Task {
                        await run {
                            let out = try await ApiClient.shared.residentEmbed(
                                key: embedKey, text: embedText,
                                token: state.token ?? "")
                            status = out.key + " · " + out.embedder
                            embedText = ""
                        }
                    }
                }.disabled(embedKey.isEmpty || embedText.isEmpty)
                TextField(L10n.t("res.search.ph", state.language),
                          text: $query)
                    .textFieldStyle(.roundedBorder)
                Button(L10n.t("res.search.go", state.language)) {
                    Task {
                        await run {
                            matches = try await ApiClient.shared.residentSearch(
                                query: query, token: state.token ?? "").matches
                        }
                    }
                }.disabled(query.isEmpty)
                ForEach(matches, id: \.key) { m in
                    Text(m.key + " · " + String((m.score * 1000).rounded() / 1000))
                        .font(.caption2)
                }

                if let status { Text(status).font(.caption) }
                if let error {
                    Text(error).font(.caption).foregroundStyle(Color.red)
                }
            }
            .padding(20)
        }
        .task { await load() }
    }

    private func run(_ body: () async throws -> Void) async {
        error = nil
        do { try await body(); await load() }
        catch { self.error = "\(error.localizedDescription)" }
    }

    private func load() async {
        do {
            posture = try await ApiClient.shared.residentPosture(token: state.token ?? "")
            tasks = try await ApiClient.shared.residentTasks(token: state.token ?? "")
            datasets = try await ApiClient.shared.residentDatasets(token: state.token ?? "")
        } catch { self.error = "\(error.localizedDescription)" }
    }
}
