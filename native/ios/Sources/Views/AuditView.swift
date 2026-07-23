import SwiftUI

/// The tamper-evident audit chain: an integrity badge + recent entries.
struct AuditView: View {
    @EnvironmentObject var state: AppState
    @State private var intact: Bool?
    @State private var entries: [AuditEntry] = []
    @State private var loading = true

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Audit").font(.title2.bold()).foregroundStyle(Theme.txt)
                Text("Every vault action is hash-chained. Verify recomputes the whole chain.")
                    .font(.footnote).foregroundStyle(Theme.t2)

                HStack(spacing: 10) {
                    Image(systemName: intact == false ? "xmark.seal.fill" : "checkmark.seal.fill")
                        .font(.system(size: 28))
                        .foregroundStyle(intact == false ? Theme.red : Theme.green)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(loading ? "Verifying…" : (intact == true ? "Chain intact" : "Chain broken"))
                            .font(.headline).foregroundStyle(Theme.txt)
                        Text("\(entries.count) recorded events").font(.caption).foregroundStyle(Theme.t2)
                    }
                    Spacer()
                }.card()

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

    private func load() async {
        guard let token = state.token else { return }
        loading = true
        intact = (try? await ApiClient.shared.auditVerify(token: token))?.intact
        entries = (try? await ApiClient.shared.auditEntries(token: token)) ?? []
        loading = false
    }
}
