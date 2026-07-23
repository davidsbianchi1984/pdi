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
import com.pdi.vault.ui.VaultScreen
import com.pdi.vault.ui.WelcomeScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            PdiTheme {
                val vm: VaultViewModel = viewModel()
                if (!vm.isSignedIn) {
                    WelcomeScreen(vm)
                } else {
                    HomeShell(vm)
                }
            }
        }
    }
}

@androidx.compose.runtime.Composable
private fun HomeShell(vm: VaultViewModel) {
    var tab by remember { mutableIntStateOf(0) }
    val tabs = listOf(
        Triple("Overview", Icons.Filled.GridView, 0),
        Triple("Vault", Icons.Filled.Lock, 1),
        Triple("Audit", Icons.Filled.VerifiedUser, 2),
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
                else -> AuditScreen(vm)
            }
        }
    }
}
