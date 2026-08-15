import SwiftUI

/// The tamper-evident audit chain: an integrity badge + recent entries.
struct AuditView: View {
    @EnvironmentObject var state: AppState
    @State private var intact: Bool?
    @State private var acceptance: AcceptanceReport?
    @State private var entries: [AuditEntry] = []
    @State private var loading = true

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(L10n.t("tab.audit", state.language)).font(.title2.bold()).foregroundStyle(Theme.txt)
                ProblemReportingCard()
                Text(L10n.t("naud.desc", state.language))
                    .font(.footnote).foregroundStyle(Theme.t2)

                HStack(spacing: 10) {
                    Image(systemName: intact == false ? "xmark.seal.fill" : "checkmark.seal.fill")
                        .font(.system(size: 28))
                        .foregroundStyle(intact == false ? Theme.red : Theme.green)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(loading ? L10n.t("naud.verifying", state.language) : (intact == true ? L10n.t("naud.intact", state.language) : L10n.t("naud.broken", state.language)))
                            .font(.headline).foregroundStyle(Theme.txt)
                        Text(L10n.t("naud.events", state.language).replacingOccurrences(of: "{n}", with: "\(entries.count)")).font(.caption).foregroundStyle(Theme.t2)
                    }
                    Spacer()
                }.card()

                // Section 10, beside the chain it verifies.
                if let acceptance {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(L10n.t("naud.accept", state.language))
                            .font(.headline).foregroundStyle(Theme.txt)
                        Text("\(acceptance.passing) / \(acceptance.of)")
                            .font(.subheadline)
                            .foregroundStyle(acceptance.clean ? Theme.green : Theme.red)
                        ForEach(acceptance.checks) { check in
                            HStack(alignment: .top, spacing: 8) {
                                Image(systemName: check.passed
                                      ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundStyle(check.passed ? Theme.green : Theme.red)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(check.says).font(.caption)
                                        .foregroundStyle(Theme.txt)
                                    Text(check.detail).font(.caption2)
                                        .foregroundStyle(Theme.t2)
                                }
                            }
                        }
                    }.card()
                }

                if loading {
                    ProgressView().tint(Theme.brandA).frame(maxWidth: .infinity)
                } else {
                    ForEach(entries.suffix(30).reversed(), id: \.seq) { e in
                        HStack(spacing: 10) {
                            Text("#\(e.seq)").font(.caption.monospaced()).foregroundStyle(Theme.t3)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(e.action).font(.subheadline.bold()).foregroundStyle(Theme.txt)
                                if let ref = e.ref, !ref.isEmpty {
                                    Text(ref).font(.caption).foregroundStyle(Theme.t2)
                                }
                            }
                            Spacer()
                            if let cat = e.category {
                                Text(cat).font(.caption2.bold())
                                    .padding(.horizontal, 7).padding(.vertical, 3)
                                    .background(Theme.brandA.opacity(0.16)).foregroundStyle(Theme.brandA)
                                    .clipShape(Capsule())
                            }
                        }.card()
                    }
                }
            }.padding(20)
        }
        .task { await load() }
        .refreshable { await load() }
    }

    /// The five acceptance criteria, run on this deployment. Nil until the
    /// screen has loaded, and left nil on failure rather than shown as a
    /// clean zero — an acceptance report that cannot be produced is not the
    /// same as one that passed.
    private func load() async {
        guard let token = state.token else { return }
        loading = true
        intact = (try? await ApiClient.shared.auditVerify(token: token))?.intact
        entries = (try? await ApiClient.shared.auditEntries(token: token)) ?? []
        // Section 10, beside the chain it verifies. A phone is where somebody
        // asks the awkward question in a meeting, which is exactly when
        // "our CI is green" is the wrong answer.
        acceptance = try? await ApiClient.shared.acceptance(token: token)
        loading = false
    }
}
