import SwiftUI

@main
struct PdiVaultApp: App {
    @StateObject private var state = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(state)
                .preferredColorScheme(.dark)
        }
    }
}

/// Switches between the token sign-in and the signed-in tab bar.
struct RootView: View {
    @EnvironmentObject var state: AppState

    var body: some View {
        ZStack {
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
        }
    }
}
