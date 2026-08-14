import SwiftUI

@main
struct PdiVaultApp: App {
    @StateObject private var state = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(state)
                .preferredColorScheme(.dark)
                // What the buffer is for. Detached and unawaited: a
                // diagnostic must never be the reason a launch is slow, and
                // `send` returns an outcome rather than throwing, so there is
                // nothing here to handle. It answers `.awaitingNotice` until
                // somebody has been told and chosen.
                .task { await Problems.send() }
        }
    }
}

/// Switches between the token sign-in and the signed-in tab bar.
struct RootView: View {
    @EnvironmentObject var state: AppState

    var body: some View {
        ZStack(alignment: .top) {
            Theme.bg.ignoresSafeArea()
            if state.isSignedIn {
                TabView {
                    OverviewView().tabItem { Label(L10n.t("tab.overview", state.language), systemImage: "circle.grid.cross") }
                    VaultView().tabItem { Label(L10n.t("tab.vault", state.language), systemImage: "lock.rectangle.stack") }
                    AuditView().tabItem { Label(L10n.t("tab.audit", state.language), systemImage: "checkmark.seal") }
                    SourcesView().tabItem { Label(L10n.t("tab.sources", state.language), systemImage: "figure.walk.motion") }
                    TransfersView().tabItem { Label(L10n.t("tab.transfers", state.language), systemImage: "arrow.up.arrow.down.circle") }
                }
                .tint(Theme.brandA)
            } else {
                WelcomeView()
            }
            // Above the tab bar and above the welcome flow both: a stale
            // backend breaks the screens a signed-out person meets first,
            // and telling them only after they get in would be telling
            // them after the part that fails.
            VersionGuardBar()
        }
    }
}
