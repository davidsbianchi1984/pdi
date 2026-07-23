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
                    OverviewView().tabItem { Label("Overview", systemImage: "circle.grid.cross") }
                    VaultView().tabItem { Label("Vault", systemImage: "lock.rectangle.stack") }
                    AuditView().tabItem { Label("Audit", systemImage: "checkmark.seal") }
                    RobotsView().tabItem { Label("Robots", systemImage: "figure.walk.motion") }
                    TransfersView().tabItem { Label("Transfers", systemImage: "arrow.up.arrow.down.circle") }
                }
                .tint(Theme.brandA)
            } else {
                WelcomeView()
            }
        }
    }
}
