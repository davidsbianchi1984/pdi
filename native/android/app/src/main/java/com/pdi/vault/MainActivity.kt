package com.pdi.vault

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.GridView
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Face
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.VerifiedUser
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.lifecycle.viewmodel.compose.viewModel
import com.pdi.vault.ui.Pdi
import com.pdi.vault.ui.PdiTheme
import com.pdi.vault.ui.AuditScreen
import com.pdi.vault.ui.OverviewScreen
import com.pdi.vault.ui.SourcesScreen
import com.pdi.vault.ui.TransfersScreen
import com.pdi.vault.ui.VaultScreen
import com.pdi.vault.ui.WelcomeScreen
import com.pdi.vault.ui.VersionGuardBar

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // The recorder holds the application context so `record` can keep the
        // same three arguments it takes on iOS and Windows. Attaching is the
        // price of that: without this line the Android shell would record
        // nothing at all, and record it quietly — the recorder refuses to
        // crash over a diagnostic, so a missing attach has no symptom.
        Problems.attach(this)
        // What the buffer is for. Off the main thread because `send` blocks on
        // a socket, and fire-and-forget because a diagnostic must never be the
        // reason a launch is slow. It answers AWAITING_NOTICE until somebody
        // has been told and chosen.
        Thread { Problems.send(BuildConfig.VERSION_NAME) }.start()
        enableEdgeToEdge()
        setContent {
            PdiTheme {
                val vm: VaultViewModel = viewModel()
                // Over the tab bar and over the welcome flow both: a stale
                // backend breaks the screens a signed-out person meets
                // first, and saying so only after they get in would be
                // saying it after the part that fails.
                Box {
                    if (!vm.isSignedIn) {
                        WelcomeScreen(vm)
                    } else {
                        HomeShell(vm)
                    }
                    VersionGuardBar(vm.language)
                }
            }
        }
    }
}

@androidx.compose.runtime.Composable
private fun HomeShell(vm: VaultViewModel) {
    var tab by remember { mutableIntStateOf(0) }
    val tabs = listOf(
        Triple(L10n.t("tab.overview", vm.language), Icons.Filled.GridView, 0),
        Triple(L10n.t("tab.vault", vm.language), Icons.Filled.Lock, 1),
        Triple(L10n.t("tab.audit", vm.language), Icons.Filled.VerifiedUser, 2),
        Triple(L10n.t("tab.sources", vm.language), Icons.Filled.Face, 3),
        Triple(L10n.t("tab.transfers", vm.language), Icons.Filled.Send, 4),
    )
    Scaffold(
        containerColor = Pdi.ScrBot,
        bottomBar = {
            NavigationBar(containerColor = Color(0xFF0B1220)) {
                tabs.forEach { (label, icon, index) ->
                    NavigationBarItem(
                        selected = tab == index,
                        onClick = { tab = index },
                        icon = { Icon(icon, contentDescription = label) },
                        label = { Text(label) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = Pdi.BrandA,
                            selectedTextColor = Pdi.BrandA,
                            unselectedIconColor = Pdi.T2,
                            unselectedTextColor = Pdi.T2,
                            indicatorColor = Color(0x337C5CFF),
                        ),
                    )
                }
            }
        },
    ) { pad ->
        Box(Modifier.fillMaxSize().background(Pdi.Bg).padding(pad)) {
            when (tab) {
                0 -> OverviewScreen(vm)
                1 -> VaultScreen(vm)
                2 -> AuditScreen(vm)
                3 -> SourcesScreen(vm)
                else -> TransfersScreen(vm)
            }
        }
    }
}
