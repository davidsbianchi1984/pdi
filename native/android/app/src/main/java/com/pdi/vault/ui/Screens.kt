package com.pdi.vault.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pdi.vault.ApiClient
import com.pdi.vault.AuditEntry
import com.pdi.vault.ComplianceProgram
import com.pdi.vault.Transfer
import com.pdi.vault.Robot
import com.pdi.vault.RobotSpec
import com.pdi.vault.VaultViewModel

@Composable
private fun screenScroll(content: @Composable ColumnScope.() -> Unit) =
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        content = content,
    )

@Composable
private fun BrandButton(text: String, enabled: Boolean = true, busy: Boolean = false, onClick: () -> Unit) {
    Box(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(13.dp))
            .background(Pdi.Card.copy(alpha = 0.4f))
            .then(if (enabled) Modifier.background(Pdi.Brand) else Modifier)
            .clickable(enabled = enabled && !busy) { onClick() }
            .padding(vertical = 14.dp),
        contentAlignment = Alignment.Center,
    ) {
        if (busy) CircularProgressIndicator(color = Color.White, strokeWidth = 2.dp, modifier = Modifier.size(20.dp))
        else Text(text, color = Color.White, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun labeledField(label: String, value: String, placeholder: String, onChange: (String) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(label, color = Pdi.T2, fontSize = 12.sp)
        OutlinedTextField(
            value = value, onValueChange = onChange, singleLine = true,
            placeholder = { Text(placeholder, color = Pdi.T3) },
            modifier = Modifier.fillMaxWidth(),
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = Pdi.Txt, unfocusedTextColor = Pdi.Txt,
                focusedBorderColor = Pdi.BrandA, unfocusedBorderColor = Pdi.Line,
                focusedContainerColor = Pdi.ScrBot, unfocusedContainerColor = Pdi.ScrBot,
            ),
        )
    }
}

// ---- Welcome / token sign-in ----

@Composable
fun WelcomeScreen(vm: VaultViewModel) {
    var token by remember { mutableStateOf("") }
    var base by remember { mutableStateOf(vm.baseURL) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Box(Modifier.fillMaxSize().background(Pdi.Bg)) {
        screenScroll {
            Spacer(Modifier.height(28.dp))
            Box(Modifier.align(Alignment.CenterHorizontally).size(84.dp).clip(CircleShape).background(Pdi.Brand),
                contentAlignment = Alignment.Center) {
                Text("🔒", fontSize = 34.sp)
            }
            Text("Sign in to your vault", color = Pdi.Txt, fontSize = 22.sp,
                fontWeight = FontWeight.Bold, modifier = Modifier.align(Alignment.CenterHorizontally))
            Text("Paste the tenant token you were issued. It authorizes every call.",
                color = Pdi.T2, fontSize = 13.sp, modifier = Modifier.align(Alignment.CenterHorizontally))

            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                labeledField("Vault token", token, "pdi_…") { token = it }
                labeledField("Server", base, "http://10.0.2.2:8000") { base = it }
            }
            error?.let { Text(it, color = Pdi.Red, fontSize = 13.sp) }
            BrandButton("Unlock", enabled = token.isNotBlank(), busy = busy) {
                error = null
                vm.signIn(token, base, onError = { error = it }, onBusy = { busy = it })
            }
            Text("Start the backend:  PDI_CORS_ORIGINS=* uvicorn pdi.api:app",
                color = Pdi.T3, fontSize = 10.sp)
        }
    }
}

// ---- Overview ----

@Composable
fun OverviewScreen(vm: VaultViewModel) {
    var count by remember { mutableStateOf<Int?>(null) }
    var intact by remember { mutableStateOf<Boolean?>(null) }
    var loaded by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        vm.call({ ApiClient.keys(vm.token!!) }) { r -> count = r.getOrNull()?.size }
        vm.call({ ApiClient.auditVerify(vm.token!!) }) { r -> intact = r.getOrNull(); loaded = true }
    }
    screenScroll {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Box(Modifier.size(8.dp).clip(CircleShape).background(Pdi.Green))
            Text("Vault unlocked", color = Pdi.Green, fontSize = 12.sp, fontWeight = FontWeight.Bold)
        }
        Text("Your vault", color = Pdi.Txt, fontSize = 28.sp, fontWeight = FontWeight.Bold)
        Text("Records are sealed at rest; every access is hash-chained in the audit log.",
            color = Pdi.T2, fontSize = 14.sp)

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            statCard(Modifier.weight(1f), "Records", if (!loaded) "—" else (count ?: 0).toString(), Pdi.BrandA)
            statCard(Modifier.weight(1f), "Audit",
                if (!loaded) "—" else if (intact == false) "Broken" else "Intact",
                if (intact == false) Pdi.Red else Pdi.Green)
        }

        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("Token", color = Pdi.Txt, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            Text(masked(vm.token ?: ""), color = Pdi.T2, fontSize = 13.sp)
            Text(vm.baseURL, color = Pdi.T3, fontSize = 12.sp)
        }
        OutlinedButton(onClick = { vm.signOut() }, modifier = Modifier.fillMaxWidth(),
            border = androidx.compose.foundation.BorderStroke(1.dp, Pdi.Line)) {
            Text("Sign out", color = Pdi.T2)
        }
    }
}

private fun masked(t: String): String =
    if (t.length > 8) t.take(6) + "…" + t.takeLast(4) else "••••"

@Composable
private fun statCard(modifier: Modifier, label: String, value: String, tint: Color) {
    Column(modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(value, color = tint, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text(label, color = Pdi.T2, fontSize = 12.sp)
    }
}

// ---- Vault ----

@Composable
fun VaultScreen(vm: VaultViewModel) {
    var keys by remember { mutableStateOf<List<String>?>(null) }
    var newKey by remember { mutableStateOf("") }
    var newValue by remember { mutableStateOf("") }
    var revealed by remember { mutableStateOf<Map<String, String>>(emptyMap()) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    fun reload() { vm.call({ ApiClient.keys(vm.token!!) }) { r -> keys = r.getOrDefault(emptyList()) } }
    LaunchedEffect(Unit) { reload() }

    screenScroll {
        Text("Vault", color = Pdi.Txt, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text("Store a value — it is sealed at rest with AES-256-GCM.", color = Pdi.T2, fontSize = 13.sp)
        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            labeledField("Key", newKey, "e.g. ssn") { newKey = it }
            labeledField("Value", newValue, "plaintext to seal") { newValue = it }
            BrandButton("Seal record", enabled = newKey.isNotBlank() && newValue.isNotBlank(), busy = busy) {
                busy = true; error = null
                vm.call({ ApiClient.putRecord(vm.token!!, newKey, newValue) }) { r ->
                    busy = false
                    r.onSuccess { newKey = ""; newValue = ""; reload() }
                     .onFailure { error = it.message }
                }
            }
        }
        error?.let { Text(it, color = Pdi.Red, fontSize = 13.sp) }

        when {
            keys == null -> CircularProgressIndicator(color = Pdi.BrandA, modifier = Modifier.size(22.dp))
            keys!!.isEmpty() -> Column(Modifier.card()) {
                Text("No records yet — seal one above.", color = Pdi.T2, fontSize = 13.sp)
            }
            else -> keys!!.forEach { key ->
                Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(key, color = Pdi.Txt, fontSize = 14.sp, fontWeight = FontWeight.Bold,
                            modifier = Modifier.weight(1f))
                        TextButton(onClick = {
                            if (revealed.containsKey(key)) revealed = revealed - key
                            else vm.call({ ApiClient.record(vm.token!!, key) }) { r ->
                                r.getOrNull()?.let { revealed = revealed + (key to it.value) }
                            }
                        }) { Text(if (revealed.containsKey(key)) "Hide" else "Reveal", color = Pdi.BrandA, fontSize = 12.sp) }
                        TextButton(onClick = {
                            vm.call({ ApiClient.deleteRecord(vm.token!!, key) }) { _ ->
                                revealed = revealed - key; reload()
                            }
                        }) { Text("Delete", color = Pdi.Red, fontSize = 12.sp) }
                    }
                    revealed[key]?.let { v ->
                        Text(v, color = Pdi.T2, fontSize = 12.sp,
                            modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(9.dp))
                                .background(Pdi.ScrBot).padding(10.dp))
                    }
                }
            }
        }
    }
}

// ---- Audit ----

@Composable
fun AuditScreen(vm: VaultViewModel) {
    var intact by remember { mutableStateOf<Boolean?>(null) }
    var entries by remember { mutableStateOf<List<AuditEntry>?>(null) }
    LaunchedEffect(Unit) {
        vm.call({ ApiClient.auditVerify(vm.token!!) }) { r -> intact = r.getOrNull() }
        vm.call({ ApiClient.auditEntries(vm.token!!) }) { r -> entries = r.getOrDefault(emptyList()) }
    }
    screenScroll {
        Text("Audit", color = Pdi.Txt, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text("Every vault action is hash-chained. Verify recomputes the whole chain.",
            color = Pdi.T2, fontSize = 13.sp)
        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(
                when (intact) { null -> "Verifying…"; true -> "Chain intact"; else -> "Chain broken" },
                color = if (intact == false) Pdi.Red else Pdi.Green, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            Text("${entries?.size ?: 0} recorded events", color = Pdi.T2, fontSize = 12.sp)
        }
        when {
            entries == null -> CircularProgressIndicator(color = Pdi.BrandA, modifier = Modifier.size(22.dp))
            else -> entries!!.takeLast(30).reversed().forEach { e ->
                Row(Modifier.card(), verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("#${e.seq}", color = Pdi.T3, fontSize = 12.sp)
                    Column(Modifier.weight(1f)) {
                        Text(e.action, color = Pdi.Txt, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                        e.ref?.takeIf { it.isNotBlank() }?.let { Text(it, color = Pdi.T2, fontSize = 12.sp) }
                    }
                    e.category?.let { Text(it, color = Pdi.BrandA, fontSize = 11.sp, fontWeight = FontWeight.Bold) }
                }
            }
        }
    }
}

// ---- Robots (vault-backed data sources) ----

@Composable
fun RobotsScreen(vm: VaultViewModel) {
    var catalog by remember { mutableStateOf<List<RobotSpec>>(emptyList()) }
    var chosen by remember { mutableStateOf("saros_20") }
    var robots by remember { mutableStateOf<List<Robot>>(emptyList()) }
    var lastKey by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    fun reload() { vm.call({ ApiClient.robots(vm.token!!) }) { r -> robots = r.getOrDefault(emptyList()) } }
    LaunchedEffect(Unit) {
        vm.call({ ApiClient.roboticsCatalog(vm.token!!) }) { r -> catalog = r.getOrDefault(emptyList()) }
        reload()
    }

    fun seal(rob: Robot, kind: String, content: String) {
        error = null
        vm.call({ ApiClient.ingest(vm.token!!, rob.id, kind, content) }) { r ->
            r.onSuccess { lastKey = it.key }.onFailure { error = it.message }
            reload()
        }
    }

    screenScroll {
        Text("Robots", color = Pdi.Txt, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text("What your robots see stays sealed — every intake is encrypted at rest and hash-chained in the audit log.",
            color = Pdi.T2, fontSize = 13.sp)

        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Bind a robot", color = Pdi.Txt, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            catalog.chunked(2).forEach { row ->
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    row.forEach { s ->
                        FilterChip(
                            selected = chosen == s.model, onClick = { chosen = s.model },
                            label = { Text(s.label, fontSize = 11.sp) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = Pdi.BrandA,
                                selectedLabelColor = Color.White, labelColor = Pdi.T2,
                            ),
                        )
                    }
                }
            }
            BrandButton("Bind", enabled = catalog.isNotEmpty(), busy = busy) {
                busy = true; error = null
                vm.call({ ApiClient.bindRobot(vm.token!!, chosen) }) { r ->
                    busy = false
                    r.onFailure { error = it.message }
                    reload()
                }
            }
        }
        error?.let { Text(it, color = Pdi.Red, fontSize = 13.sp) }

        robots.forEach { rob ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(rob.name, color = Pdi.Txt, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text("${rob.collected} sealed", color = Pdi.Green, fontSize = 12.sp)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick = { seal(rob, "map", "{\"rooms\": 5}") }) {
                        Text("Seal map", color = Pdi.BrandA, fontSize = 12.sp) }
                    TextButton(onClick = { seal(rob, "snapshot", "camera still") }) {
                        Text("Snapshot", color = Pdi.BrandA, fontSize = 12.sp) }
                    TextButton(onClick = { seal(rob, "sensor_log", "steps & doors") }) {
                        Text("Sensor log", color = Pdi.BrandA, fontSize = 12.sp) }
                }
            }
        }

        lastKey?.let { key ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Sealed", color = Pdi.Txt, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                Text(key, color = Pdi.T2, fontSize = 11.sp)
                Text("Read it (audited) via Vault → the key above.", color = Pdi.T3, fontSize = 11.sp)
            }
        }
    }
}

// ---- Transfers (compliance-grade secure file transfer) ----

@Composable
fun TransfersScreen(vm: VaultViewModel) {
    var programs by remember { mutableStateOf<List<ComplianceProgram>>(emptyList()) }
    var selected by remember { mutableStateOf(setOf("hipaa")) }
    var recipient by remember { mutableStateOf("") }
    var filename by remember { mutableStateOf("") }
    var content by remember { mutableStateOf("") }
    var transfers by remember { mutableStateOf<List<Transfer>>(emptyList()) }
    var minted by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    fun reload() { vm.call({ ApiClient.transfers(vm.token!!) }) { r -> transfers = r.getOrDefault(emptyList()) } }
    LaunchedEffect(Unit) {
        vm.call({ ApiClient.compliancePrograms(vm.token!!) }) { r -> programs = r.getOrDefault(emptyList()) }
        reload()
    }

    screenScroll {
        Text("Transfers", color = Pdi.Txt, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text("Seal a file for a recipient under compliance controls. Retention follows the strictest program you pick.",
            color = Pdi.T2, fontSize = 13.sp)

        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            labeledField("Recipient", recipient, "who it's for") { recipient = it }
            labeledField("Filename", filename, "e.g. results.pdf") { filename = it }
            labeledField("Content", content, "the file body to seal") { content = it }
            Text("Programs", color = Pdi.T2, fontSize = 12.sp)
            programs.chunked(4).forEach { row ->
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    row.forEach { p ->
                        FilterChip(
                            selected = p.key in selected,
                            onClick = {
                                selected = if (p.key in selected) selected - p.key
                                           else selected + p.key
                            },
                            label = { Text(p.key.uppercase(), fontSize = 10.sp) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = Pdi.BrandA,
                                selectedLabelColor = Color.White, labelColor = Pdi.T2,
                            ),
                        )
                    }
                }
            }
            BrandButton("Seal & create",
                enabled = recipient.isNotBlank() && filename.isNotBlank()
                          && content.isNotBlank() && selected.isNotEmpty(),
                busy = busy) {
                busy = true; error = null
                vm.call({ ApiClient.createTransfer(vm.token!!, recipient, filename,
                                                    content, selected.toList()) }) { r ->
                    busy = false
                    r.onSuccess { minted = it.receiveToken
                                  recipient = ""; filename = ""; content = "" }
                     .onFailure { error = it.message }
                    reload()
                }
            }
        }
        error?.let { Text(it, color = Pdi.Red, fontSize = 13.sp) }

        minted?.let { tok ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Receive token — shown once", color = Pdi.Amber, fontSize = 15.sp,
                    fontWeight = FontWeight.Bold)
                Text(tok, color = Pdi.Txt, fontSize = 11.sp)
                Text("Hand this to the recipient out of band; it is the only way to retrieve the file.",
                    color = Pdi.T2, fontSize = 11.sp)
            }
        }

        transfers.forEach { t ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(t.filename, color = Pdi.Txt, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text(t.status.replaceFirstChar { it.uppercase() },
                        color = if (t.status == "revoked") Pdi.Red else Pdi.Green, fontSize = 12.sp)
                }
                Text("→ ${t.recipient} · ${t.programs.joinToString(" ") { it.uppercase() }}",
                    color = Pdi.T2, fontSize = 12.sp)
                t.expiresAt?.let { Text("retained until $it", color = Pdi.T3, fontSize = 11.sp) }
                if (t.status != "revoked") {
                    TextButton(onClick = {
                        vm.call({ ApiClient.revokeTransfer(vm.token!!, t.id) }) { reload() }
                    }) { Text("Revoke access", color = Pdi.Red, fontSize = 12.sp) }
                }
            }
        }
    }
}
