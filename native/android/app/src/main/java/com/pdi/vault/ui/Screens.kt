package com.pdi.vault.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pdi.vault.AccessReportRow
import com.pdi.vault.ApiClient
import com.pdi.vault.Problems
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import com.pdi.vault.ImproveState
import com.pdi.vault.KeysInfo
import com.pdi.vault.OfflinePosture
import com.pdi.vault.L10n
import com.pdi.vault.LanguageInfo
import com.pdi.vault.RecordProvenance
import com.pdi.vault.AuditEntry
import com.pdi.vault.ComplianceProgram
import com.pdi.vault.Intake
import com.pdi.vault.IntakeFile
import com.pdi.vault.Transfer
import com.pdi.vault.Robot
import com.pdi.vault.RobotSpec
import com.pdi.vault.SocialConn
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
private fun SmallAction(text: String, onClick: () -> Unit) {
    Text(text, color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold,
        modifier = Modifier.clip(RoundedCornerShape(50))
            .background(Pdi.BrandA)
            .clickable { onClick() }
            .padding(horizontal = 12.dp, vertical = 8.dp))
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

private val LANGUAGE_CHOICES = listOf(
    "en" to "English", "es" to "Español", "fr" to "Français",
    "de" to "Deutsch", "pt" to "Português", "it" to "Italiano",
    "ja" to "日本語", "zh" to "中文", "hi" to "हिन्दी", "ar" to "العربية")

@Composable
fun WelcomeScreen(vm: VaultViewModel) {
    var token by remember { mutableStateOf("") }
    var language by remember { mutableStateOf("en") }
    var base by remember { mutableStateOf(vm.baseURL) }
    // Held in composition and handed to the client, never to
    // SharedPreferences — see ApiClient.tenantKey.
    var tenantKey by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var held by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    // Nobody reading this screen has a tenant, so there is no stored
    // language to take. The device has been carrying the answer all along.
    val lang = L10n.deviceLanguage()

    Box(Modifier.fillMaxSize().background(Pdi.Bg)) {
        screenScroll {
            Spacer(Modifier.height(28.dp))
            Box(Modifier.align(Alignment.CenterHorizontally).size(84.dp).clip(CircleShape).background(Pdi.Brand),
                contentAlignment = Alignment.Center) {
                Text("🔒", fontSize = 34.sp)
            }
            Text(L10n.t("wel.title", lang), color = Pdi.Txt, fontSize = 22.sp,
                fontWeight = FontWeight.Bold, modifier = Modifier.align(Alignment.CenterHorizontally))
            Text(L10n.t("wel.sub", lang),
                color = Pdi.T2, fontSize = 13.sp, modifier = Modifier.align(Alignment.CenterHorizontally))

            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                labeledField(L10n.t("wel.token", lang), token, L10n.t("nacc.id.ph", vm.language)) { token = it }
                labeledField(L10n.t("wel.server", lang), base,
                    "http://10.0.2.2:8000") { base = it }
                // Only a vault under customer custody needs this. Leaving it
                // blank on such a vault is what every phone did until now,
                // and every record answered 428.
                labeledField(L10n.t("wel.tenantkey", lang), tenantKey,
                    L10n.t("wel.tenantkey.ph", lang)) { tenantKey = it }
                Text(L10n.t("wel.language", lang), color = Pdi.T2, fontSize = 12.sp)
                LANGUAGE_CHOICES.chunked(3).forEach { row ->
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        row.forEach { (code, label) ->
                            FilterChip(
                                selected = language == code,
                                onClick = { language = code },
                                label = { Text(label, fontSize = 11.sp) },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = Pdi.BrandA,
                                    selectedLabelColor = Color.White, labelColor = Pdi.T2,
                                ),
                            )
                        }
                    }
                }
            }
            error?.let { Text(it, color = Pdi.Red, fontSize = 13.sp) }
            // The portability door: counts and table names on the phone; the
            // document itself is what the console downloads.
            BrandButton(L10n.t("nadm.dsr", lang), enabled = true) {
                vm.call({ ApiClient.exportEverything(vm.token ?: "") }) { r ->
                    r.onSuccess { (tables, rows) ->
                        held = "$tables table(s), $rows row(s)"
                    }
                }
            }

            BrandButton(L10n.t("wel.unlock", lang), enabled = token.isNotBlank(),
                busy = busy) {
                error = null
                vm.signIn(token, base, language, tenantKey,
                    onError = { error = it }, onBusy = { busy = it })
            }
            Text(L10n.t("wel.backend", lang)
                 + "  PDI_CORS_ORIGINS=* uvicorn pdi.api:app",
                color = Pdi.T3, fontSize = 10.sp)
        }
    }
}

// ---- Overview ----

@Composable
@OptIn(ExperimentalMaterial3Api::class)
fun OverviewScreen(vm: VaultViewModel) {
    var count by remember { mutableStateOf<Int?>(null) }
    var intact by remember { mutableStateOf<Boolean?>(null) }
    var loaded by remember { mutableStateOf(false) }
    var refreshing by remember { mutableStateOf(false) }
    var languages by remember { mutableStateOf<List<LanguageInfo>>(emptyList()) }
    var language by remember { mutableStateOf("en") }
    var preTranslate by remember { mutableStateOf(true) }
    fun reload() {
        vm.call({ ApiClient.keys(vm.token!!) }) { r -> count = r.getOrNull()?.size }
        vm.call({ ApiClient.auditVerify(vm.token!!) }) { r ->
            intact = r.getOrNull(); loaded = true; refreshing = false
        }
    }
    LaunchedEffect(Unit) {
        reload()
        vm.call({ ApiClient.languages(vm.token!!) }) { r -> languages = r.getOrDefault(emptyList()) }
        vm.call({ ApiClient.language(vm.token!!) }) { r ->
            r.getOrNull()?.let { (lang, mode) ->
                language = lang; preTranslate = mode == "pre"
                vm.rememberLanguage(lang)   // chrome follows the tenant
            }
        }
    }
    PullToRefreshBox(isRefreshing = refreshing,
        onRefresh = { refreshing = true; reload() }) {
    screenScroll {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Box(Modifier.size(8.dp).clip(CircleShape).background(Pdi.Green))
            Text(L10n.t("nov.unlocked", vm.language), color = Pdi.Green, fontSize = 12.sp, fontWeight = FontWeight.Bold)
        }
        Text(L10n.t("nov.title", vm.language), color = Pdi.Txt, fontSize = 28.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("nov.sealed", vm.language),
            color = Pdi.T2, fontSize = 14.sp)

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            statCard(Modifier.weight(1f), L10n.t("nrec.t.records", vm.language), if (!loaded) "—" else (count ?: 0).toString(), Pdi.BrandA)
            statCard(Modifier.weight(1f), L10n.t("tab.audit", vm.language),
                if (!loaded) "—" else if (intact == false) L10n.t("nov.broken", vm.language) else L10n.t("nov.intact", vm.language),
                if (intact == false) Pdi.Red else Pdi.Green)
        }

        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(L10n.t("nov.token", vm.language), color = Pdi.Txt, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            Text(masked(vm.token ?: ""), color = Pdi.T2, fontSize = 13.sp)
            Text(vm.baseURL, color = Pdi.T3, fontSize = 12.sp)
        }
        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(L10n.t("wel.language", vm.language), color = Pdi.Txt, fontSize = 16.sp,
                 fontWeight = FontWeight.Bold)
            Text(L10n.t("nov.notes", vm.language),
                color = Pdi.T2, fontSize = 12.sp)
            languages.chunked(3).forEach { row ->
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    row.forEach { l ->
                        FilterChip(
                            selected = language == l.code,
                            onClick = {
                                vm.call({ ApiClient.setLanguage(vm.token!!, l.code,
                                    if (preTranslate) "pre" else "on_demand") }) {
                                    language = l.code
                                    vm.rememberLanguage(l.code)
                                }
                            },
                            label = { Text(l.label, fontSize = 11.sp) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = Pdi.BrandA,
                                selectedLabelColor = Color.White, labelColor = Pdi.T2,
                            ),
                        )
                    }
                }
            }
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(L10n.t("nov.pretrans", vm.language), color = Pdi.Txt, fontSize = 13.sp)
                    Text(L10n.t("nov.pretrans.off", vm.language),
                        color = Pdi.T2, fontSize = 10.sp)
                }
                Switch(
                    checked = preTranslate,
                    onCheckedChange = { on ->
                        preTranslate = on
                        vm.call({ ApiClient.setLanguage(vm.token!!, language,
                            if (on) "pre" else "on_demand") }) { }
                    },
                    colors = SwitchDefaults.colors(checkedTrackColor = Pdi.Green),
                )
            }
        }
        OfflinePostureCard(vm)
        ImproveCard(vm)
        AccessCard(vm)
        AdminCard(vm)
        TenantsAdminCard(vm)
        GateCard(vm)
        ContinuityCard(vm)
        PostureCard(vm)
        PositionsCard(vm)
        KeyCustodyCard(vm)
        GuideCard(vm)
        DockCard(vm)
        OutlinedButton(onClick = { vm.signOut() }, modifier = Modifier.fillMaxWidth(),
            border = androidx.compose.foundation.BorderStroke(1.dp, Pdi.Line)) {
            Text(L10n.t("action.sign_out", vm.language), color = Pdi.T2)
        }
    }
    }
}

// ---- Admin: key management (PDI_ADMIN_TOKEN, never the tenant token) ----

/**
 * What this deployment can and cannot reach.
 *
 * Offline mode was settable and unreadable: the flag existed, the guarantee
 * was written in a docstring, and there was nowhere on a phone to see the
 * answer.
 *
 *     asked     can the guarantee be turned on
 *     mattered  can it be checked
 *
 * Read-only on purpose. The posture is set in the deployment's environment,
 * not by somebody signed into the app — a switch here would imply otherwise.
 */
@Composable
fun OfflinePostureCard(vm: VaultViewModel) {
    var posture by remember { mutableStateOf<OfflinePosture?>(null) }
    LaunchedEffect(Unit) {
        vm.call({ ApiClient.offlineStatus() }) { r -> posture = r.getOrNull() }
    }
    posture?.let { p ->
        Card(colors = CardDefaults.cardColors(containerColor = Pdi.Card)) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(L10n.t("offline.title", vm.language),
                     style = MaterialTheme.typography.titleSmall)
                Text(if (p.offline) L10n.t("offline.on", vm.language)
                     else L10n.t("offline.off", vm.language),
                     color = if (p.offline) Pdi.Green else Pdi.T2, fontSize = 12.sp,
                     fontWeight = FontWeight.Bold)
                Text(p.localDestinationsAllowed, color = Pdi.T2, fontSize = 11.sp)
                p.guarantees.forEach { line ->
                    Text("\u2022 " + line, color = Pdi.T2, fontSize = 11.sp)
                }
            }
        }
    }
}

/** Customer custody of the tenant key: adopt a held key, move to KMS,
 *  hand back to deployment custody, and reseal under a fresh version.
 *  The note rendered is the wire's own sentence about who can decrypt. */
@Composable
fun KeyCustodyCard(vm: VaultViewModel) {
    var customerKey by remember { mutableStateOf("") }
    var adminToken by remember { mutableStateOf("") }
    var note by remember { mutableStateOf<String?>(null) }
    var resealLine by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        vm.call({ ApiClient.tenantKey(vm.token!!) }) { r -> note = r.getOrNull() }
    }

    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("cu.hold", vm.language), color = Pdi.Txt,
            fontSize = 16.sp, fontWeight = FontWeight.Bold)
        labeledField(L10n.t("cu.key.ph", vm.language), customerKey,
            L10n.t("cu.key.ph", vm.language)) { customerKey = it }
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            SmallAction(L10n.t("cu.hold", vm.language)) {
                if (customerKey.isNotBlank()) {
                    vm.call({ ApiClient.setTenantKey(vm.token!!, "held",
                        customerKey.trim()) }) { r ->
                        r.onSuccess { note = it }.onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("cu.kms", vm.language)) {
                vm.call({ ApiClient.setTenantKey(vm.token!!, "kms", null) }) { r ->
                    r.onSuccess { note = it }.onFailure { error = it.message }
                }
            }
            SmallAction(L10n.t("cu.handback", vm.language)) {
                vm.call({ ApiClient.surrenderTenantKey(vm.token!!) }) { r ->
                    r.onSuccess { note = it }.onFailure { error = it.message }
                }
            }
        }
        note?.let { Text(it, color = Pdi.T2, fontSize = 11.sp) }
        labeledField(L10n.t("nadm.token", vm.language), adminToken, "…") { adminToken = it }
        SmallAction(L10n.t("cu.reseal", vm.language)) {
            if (adminToken.isNotBlank()) {
                vm.call({ ApiClient.resealUnderNewKey(adminToken) }) { r ->
                    r.onSuccess { resealLine = it }.onFailure { error = it.message }
                }
            }
        }
        resealLine?.let {
            Text(L10n.t("cu.reseal.note", vm.language) + " " + it,
                color = Pdi.T2, fontSize = 11.sp)
        }
        error?.let { Text(it, color = Pdi.Red, fontSize = 12.sp) }
    }
}

/** A position built from two answers, listed, and opened — the console's
 *  whole intake is optional by design, so the smallest honest intake is
 *  an industry and a job title. */
@Composable
fun PositionsCard(vm: VaultViewModel) {
    var industry by remember { mutableStateOf("") }
    var jobTitle by remember { mutableStateOf("") }
    var line by remember { mutableStateOf<String?>(null) }
    var savedLine by remember { mutableStateOf<String?>(null) }
    var firstId by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    fun list() {
        vm.call({ ApiClient.listPositions(vm.token!!) }) { r ->
            r.onSuccess { (n, first) ->
                savedLine = if (n == 0) L10n.t("pos.none", vm.language)
                    else L10n.t("pos.saved", vm.language) + " $n"
                firstId = first
            }
        }
    }
    LaunchedEffect(Unit) { list() }

    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("pos.build", vm.language), color = Pdi.Txt,
            fontSize = 16.sp, fontWeight = FontWeight.Bold)
        labeledField(L10n.t("pos.industry", vm.language), industry,
            L10n.t("pos.industry", vm.language)) { industry = it }
        labeledField(L10n.t("pos.jobtitle", vm.language), jobTitle,
            L10n.t("pos.jobtitle", vm.language)) { jobTitle = it }
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            SmallAction(L10n.t("pos.build", vm.language)) {
                if (industry.isNotBlank()) {
                    vm.call({ ApiClient.buildPosition(vm.token!!,
                        industry.trim(), jobTitle.trim()) }) { r ->
                        r.onSuccess { line = it; list() }
                            .onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("pos.open", vm.language)) {
                firstId?.let { id ->
                    vm.call({ ApiClient.getPosition(vm.token!!, id) }) { r ->
                        r.onSuccess { line = it }
                            .onFailure { error = it.message }
                    }
                }
            }
        }
        line?.let {
            Text(L10n.t("pos.blueprint", vm.language) + " " + it,
                color = Pdi.T2, fontSize = 11.sp)
        }
        savedLine?.let { Text(it, color = Pdi.T2, fontSize = 11.sp) }
        error?.let { Text(it, color = Pdi.Red, fontSize = 12.sp) }
    }
}

/** The deployment's own account of itself: health, the hosting mode it
 *  is in and could move to, what went out through operations, the audit
 *  vocabulary, and whether the paperwork is on file. */
@Composable
fun PostureCard(vm: VaultViewModel) {
    var healthLine by remember { mutableStateOf<String?>(null) }
    var modes by remember { mutableStateOf<List<HostingModeK>>(emptyList()) }
    var mine by remember { mutableStateOf<HostingModeK?>(null) }
    var historyCount by remember { mutableStateOf<Int?>(null) }
    var tid by remember { mutableStateOf("") }
    var opsLine by remember { mutableStateOf<String?>(null) }
    var schemaLine by remember { mutableStateOf<String?>(null) }
    var baaLine by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        vm.call({ ApiClient.health() }) { r -> healthLine = r.getOrNull() }
        vm.call({ ApiClient.hostingModes() }) { r ->
            modes = r.getOrDefault(emptyList())
        }
        vm.call({ ApiClient.auditSchema() }) { r -> schemaLine = r.getOrNull() }
        vm.call({ ApiClient.operations(vm.token!!) }) { r ->
            r.onSuccess { n ->
                opsLine = if (n == 0) L10n.t("op.none", vm.language)
                    else L10n.t("op.events", vm.language) + " $n"
            }
        }
    }

    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("ov.health", vm.language), color = Pdi.Txt,
            fontSize = 16.sp, fontWeight = FontWeight.Bold)
        healthLine?.let { Text(it, color = Pdi.T2, fontSize = 11.sp) }

        Text(L10n.t("cu.where", vm.language), color = Pdi.Txt,
            fontSize = 14.sp, fontWeight = FontWeight.Bold)
        labeledField(L10n.t("adm.tenant.ph", vm.language), tid,
            L10n.t("adm.tenant.ph", vm.language)) { tid = it }
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            SmallAction(L10n.t("cu.where", vm.language)) {
                if (tid.isNotBlank()) {
                    vm.call({ ApiClient.hosting(vm.token!!, tid.trim()) }) { r ->
                        r.onSuccess { mine = it }.onFailure { error = it.message }
                    }
                    vm.call({ ApiClient.hostingHistory(vm.token!!, tid.trim()) }) { r ->
                        historyCount = r.getOrNull()
                    }
                }
            }
            SmallAction(L10n.t("cu.deploy", vm.language)) {
                vm.call({ ApiClient.recordDeployment(vm.token!!) }) { r ->
                    r.onFailure { error = it.message }
                }
            }
        }
        mine?.let { m ->
            Text("${m.title} \u2014 ${m.means} \u00b7 ${m.price}",
                color = Pdi.T2, fontSize = 11.sp)
            if (m.freeBecause.isNotEmpty()) {
                Text(L10n.t("cu.free", vm.language) + " " + m.freeBecause,
                    color = Pdi.T2, fontSize = 11.sp)
            }
            Text(L10n.t("cu.we", vm.language) + " " + m.we,
                color = Pdi.T2, fontSize = 10.sp)
            Text(L10n.t("cu.you", vm.language) + " " + m.you,
                color = Pdi.T2, fontSize = 10.sp)
        }
        historyCount?.let { Text(it.toString(), color = Pdi.T3, fontSize = 10.sp) }
        // Moving is one press per mode the deployment offers, priced on the
        // button the way the console prices it.
        modes.chunked(2).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                row.forEach { m ->
                    SmallAction("${m.title} \u00b7 ${m.price}") {
                        if (tid.isNotBlank()) {
                            vm.call({ ApiClient.setHosting(vm.token!!,
                                tid.trim(), m.id) }) { r ->
                                r.onFailure { error = it.message }
                            }
                        }
                    }
                }
            }
        }

        Text(L10n.t("op.title", vm.language), color = Pdi.Txt,
            fontSize = 14.sp, fontWeight = FontWeight.Bold)
        opsLine?.let { Text(it, color = Pdi.T2, fontSize = 11.sp) }
        schemaLine?.let {
            Text(L10n.t("au.actions", vm.language) + " " + it,
                color = Pdi.T2, fontSize = 11.sp)
        }
        SmallAction(L10n.t("cu.onfile", vm.language)) {
            vm.call({ ApiClient.baaStatus(vm.token!!) }) { r ->
                r.onSuccess { line ->
                    baaLine = line.ifEmpty { L10n.t("cu.no", vm.language) }
                }.onFailure { error = it.message }
            }
        }
        baaLine?.let { Text(it, color = Pdi.T2, fontSize = 11.sp) }
        error?.let { Text(it, color = Pdi.Red, fontSize = 12.sp) }
    }
}

/** Bequests through their whole life — recorded, activated by the
 *  executor, taken back, redeemed by the heir — plus contributions, the
 *  snapshot pair, and the retention ops. */
@Composable
fun ContinuityCard(vm: VaultViewModel) {
    var rows by remember { mutableStateOf<List<BequestK>>(emptyList()) }
    var grantee by remember { mutableStateOf("") }
    var prefixes by remember { mutableStateOf("") }
    var note by remember { mutableStateOf("") }
    var adminToken by remember { mutableStateOf("") }
    var ref by remember { mutableStateOf("") }
    var mintedGrant by remember { mutableStateOf<String?>(null) }
    var grantTok by remember { mutableStateOf("") }
    var custKey by remember { mutableStateOf("") }
    var heirKeys by remember { mutableStateOf<List<String>>(emptyList()) }
    var readBack by remember { mutableStateOf<String?>(null) }
    var contribSource by remember { mutableStateOf("") }
    var contribRef by remember { mutableStateOf("") }
    var contribLine by remember { mutableStateOf<String?>(null) }
    var opsLine by remember { mutableStateOf<String?>(null) }
    var status by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    fun reload() {
        vm.call({ ApiClient.bequests(vm.token!!) }) { r ->
            rows = r.getOrDefault(emptyList())
        }
        vm.call({ ApiClient.contributions(vm.token!!) }) { r ->
            r.onSuccess { n ->
                contribLine = L10n.t("bri.held", vm.language)
                    .replace("{n}", n.toString())
            }
        }
    }
    LaunchedEffect(Unit) { reload() }

    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("co.bequests", vm.language), color = Pdi.Txt,
            fontSize = 16.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("co.bequests.note", vm.language), color = Pdi.T2, fontSize = 11.sp)
        if (rows.isEmpty()) {
            Text(L10n.t("co.nothing", vm.language), color = Pdi.T2, fontSize = 11.sp)
        }
        rows.forEach { b ->
            Text(L10n.t("co.wouldopen", vm.language) + " "
                + b.prefixes.joinToString(", "),
                color = Pdi.T3, fontSize = 9.sp)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically) {
                Text(b.grantee + " \u00b7 " + L10n.t(
                    if (b.revoked) "co.revoke"
                    else if (b.activated) "co.inforce" else "co.dormant",
                    vm.language), color = Pdi.T2, fontSize = 11.sp)
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    if (!b.revoked) {
                        SmallAction(L10n.t("co.revoke", vm.language)) {
                            vm.call({ ApiClient.revokeBequest(vm.token!!, b.id) }) { reload() }
                        }
                    }
                    // The executor's press, one per dormant row; the taking
                    // back, one per row in force.
                    if (!b.activated && !b.revoked) {
                        SmallAction(L10n.t("co.activate", vm.language)) {
                            if (adminToken.isNotBlank() && ref.isNotBlank()) {
                                vm.call({ ApiClient.activateBequest(adminToken,
                                    b.id, ref.trim()) }) { r ->
                                    r.onSuccess {
                                        mintedGrant = it.grantToken; reload()
                                    }.onFailure { error = it.message }
                                }
                            }
                        }
                    }
                    if (b.activated && !b.revoked) {
                        SmallAction(L10n.t("co.revoke.grant", vm.language)) {
                            if (adminToken.isNotBlank()) {
                                vm.call({ ApiClient.revokeBequestGrant(adminToken,
                                    b.id) }) { reload() }
                            }
                        }
                    }
                }
            }
        }
        labeledField(L10n.t("co.grantee.ph", vm.language), grantee,
            L10n.t("co.grantee.ph", vm.language)) { grantee = it }
        labeledField(L10n.t("co.prefixes.ph", vm.language), prefixes,
            L10n.t("co.prefixes.ph", vm.language)) { prefixes = it }
        labeledField(L10n.t("co.note.ph", vm.language), note,
            L10n.t("co.note.ph", vm.language)) { note = it }
        SmallAction(L10n.t("co.record", vm.language)) {
            if (grantee.isNotBlank() && prefixes.isNotBlank()) {
                vm.call({ ApiClient.createBequest(vm.token!!, grantee.trim(),
                    prefixes.split(",").map { it.trim() }.filter { it.isNotEmpty() },
                    note.trim().ifEmpty { null }) }) { r ->
                    r.onSuccess { grantee = ""; prefixes = ""; note = ""; reload() }
                        .onFailure { error = it.message }
                }
            }
        }

        Text(L10n.t("co.activation", vm.language), color = Pdi.Txt,
            fontSize = 14.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("co.activation.note", vm.language), color = Pdi.T2, fontSize = 11.sp)
        labeledField(L10n.t("co.admin.ph", vm.language), adminToken, "…") { adminToken = it }
        labeledField(L10n.t("co.ref.ph", vm.language), ref,
            L10n.t("co.ref.ph", vm.language)) { ref = it }
        mintedGrant?.let {
            Text(L10n.t("co.minted", vm.language) + " "
                + L10n.t("co.minted.note", vm.language),
                color = Pdi.T2, fontSize = 10.sp)
            Text(it, color = Pdi.Txt, fontSize = 10.sp)
        }

        // The heir's side: two separate secrets, and one without the other
        // opens nothing.
        Text(L10n.t("co.redeem", vm.language), color = Pdi.Txt,
            fontSize = 14.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("co.redeem.note", vm.language), color = Pdi.T2, fontSize = 11.sp)
        labeledField(L10n.t("co.grant.ph", vm.language), grantTok,
            L10n.t("co.grant.ph", vm.language)) { grantTok = it }
        labeledField(L10n.t("co.custkey.ph", vm.language), custKey,
            L10n.t("co.custkey.ph", vm.language)) { custKey = it }
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            SmallAction(L10n.t("co.whatopen", vm.language)) {
                if (grantTok.isNotBlank() && custKey.isNotBlank()) {
                    vm.call({ ApiClient.bequestKeys(grantTok, custKey) }) { r ->
                        r.onSuccess { heirKeys = it }
                            .onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("co.read", vm.language)) {
                heirKeys.firstOrNull()?.let { first ->
                    vm.call({ ApiClient.bequestRead(first, grantTok, custKey) }) { r ->
                        r.onSuccess { readBack = it.take(200) }
                            .onFailure { error = it.message }
                    }
                }
            }
        }
        if (heirKeys.isNotEmpty()) {
            Text(heirKeys.joinToString(", "), color = Pdi.T2, fontSize = 10.sp)
        }
        readBack?.let { Text(it, color = Pdi.T2, fontSize = 10.sp) }

        // Contributions: what the tandem products sealed in, by count and
        // key only.
        Text(L10n.t("bri.contribute", vm.language), color = Pdi.Txt,
            fontSize = 14.sp, fontWeight = FontWeight.Bold)
        contribLine?.let { Text(it, color = Pdi.T2, fontSize = 11.sp) }
        labeledField(L10n.t("bri.source", vm.language), contribSource,
            L10n.t("bri.source.ph", vm.language)) { contribSource = it }
        labeledField(L10n.t("bri.ref", vm.language), contribRef,
            L10n.t("bri.ref.ph", vm.language)) { contribRef = it }
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            SmallAction(L10n.t("bri.contribute", vm.language)) {
                if (contribSource.isNotBlank()) {
                    vm.call({ ApiClient.contribute(vm.token!!,
                        contribSource.trim(),
                        contribRef.trim().ifEmpty { null }) }) { r ->
                        r.onSuccess { key ->
                            status = L10n.t("bri.sealed", vm.language)
                                .replace("{key}", key)
                            contribSource = ""; reload()
                        }.onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("bri.withdraw", vm.language)) {
                if (contribRef.isNotBlank()) {
                    vm.call({ ApiClient.withdrawContribution(vm.token!!,
                        contribRef.trim()) }) { reload() }
                }
            }
        }

        // The custody ops: the whole tenant in hand and back, the retention
        // window, the sweep, and the demo seed.
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            SmallAction(L10n.t("cu.snapshot", vm.language)) {
                vm.call({ ApiClient.snapshotRecords(vm.token!!) }) { r ->
                    r.onSuccess { opsLine = it.toString() }
                        .onFailure { error = it.message }
                }
            }
            SmallAction(L10n.t("cu.restore", vm.language)) {
                vm.call({ ApiClient.restoreSnapshot(vm.token!!) }) { r ->
                    r.onFailure { error = it.message }
                }
            }
            SmallAction(L10n.t("ky.window", vm.language)) {
                if (adminToken.isNotBlank()) {
                    vm.call({ ApiClient.retentionPolicy(adminToken) }) { r ->
                        r.onSuccess { opsLine = it }
                            .onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("ky.sweep", vm.language)) {
                if (adminToken.isNotBlank()) {
                    vm.call({ ApiClient.retentionSweep(adminToken) }) { r ->
                        r.onSuccess { opsLine = it }
                            .onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("bri.seed", vm.language)) {
                if (adminToken.isNotBlank()) {
                    vm.call({ ApiClient.seedDemo(adminToken) }) { r ->
                        r.onSuccess { status = L10n.t("bri.seeded", vm.language) }
                            .onFailure { error = it.message }
                    }
                }
            }
        }
        opsLine?.let { Text(it, color = Pdi.T2, fontSize = 11.sp) }
        status?.let { Text(it, color = Pdi.Green, fontSize = 12.sp) }
        error?.let { Text(it, color = Pdi.Red, fontSize = 12.sp) }
    }
}

@Composable
fun TenantsAdminCard(vm: VaultViewModel) {
    var adminToken by remember { mutableStateOf("") }
    var name by remember { mutableStateOf("") }
    var tid by remember { mutableStateOf("") }
    var retention by remember { mutableStateOf("") }
    var custName by remember { mutableStateOf("") }
    var opName by remember { mutableStateOf("") }
    var effDate by remember { mutableStateOf("") }
    var made by remember { mutableStateOf<TenantMadeK?>(null) }
    var minted by remember { mutableStateOf<String?>(null) }
    var mintedNote by remember { mutableStateOf<String?>(null) }
    var baa by remember { mutableStateOf<BaaK?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("tn.create", vm.language), color = Pdi.Txt, fontSize = 16.sp,
            fontWeight = FontWeight.Bold)
        labeledField(L10n.t("nadm.token", vm.language), adminToken, "…") { adminToken = it }
        labeledField(L10n.t("co.name.ph", vm.language), name,
            L10n.t("co.name.ph", vm.language)) { name = it }
        SmallAction(L10n.t("tn.createbtn", vm.language)) {
            if (name.isNotBlank()) {
                vm.call({ ApiClient.createTenant(adminToken, name.trim()) }) { r ->
                    r.onSuccess { made = it; name = "" }
                        .onFailure { error = it.message }
                }
            }
        }
        made?.let {
            Text("${it.id} \u00b7 ${it.token}", color = Pdi.Txt, fontSize = 10.sp)
            Text(L10n.t("tn.token.note", vm.language), color = Pdi.T2, fontSize = 10.sp)
        }
        labeledField(L10n.t("adm.tenant.ph", vm.language), tid,
            L10n.t("adm.tenant.ph", vm.language)) { tid = it }
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            SmallAction(L10n.t("cu.restore.all", vm.language)) {
                vm.call({ ApiClient.restoreTenant(adminToken, tid) }) { r ->
                    r.onFailure { error = it.message }
                }
            }
            // Soft keeps the door open; hard cannot be taken back. Both
            // leave the audit chain standing.
            SmallAction(L10n.t("cu.del.soft", vm.language)) {
                vm.call({ ApiClient.deleteTenant(adminToken, tid, "soft") }) { r ->
                    r.onFailure { error = it.message }
                }
            }
            SmallAction(L10n.t("cu.del.hard", vm.language)) {
                vm.call({ ApiClient.deleteTenant(adminToken, tid, "hard") }) { r ->
                    r.onFailure { error = it.message }
                }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            SmallAction(L10n.t("cu.mint.read", vm.language)) {
                vm.call({ ApiClient.mintTenantToken(adminToken, tid, "read") }) { r ->
                    r.onSuccess { minted = it }.onFailure { error = it.message }
                }
            }
            SmallAction(L10n.t("cu.mint.write", vm.language)) {
                vm.call({ ApiClient.mintTenantToken(adminToken, tid, "write") }) { r ->
                    r.onSuccess { minted = it }.onFailure { error = it.message }
                }
            }
        }
        minted?.let { tokenShown ->
            Text(tokenShown, color = Pdi.Txt, fontSize = 10.sp)
            Text(L10n.t("cu.minted.note", vm.language), color = Pdi.T2, fontSize = 10.sp)
            SmallAction(L10n.t("cu.revoke", vm.language)) {
                vm.call({ ApiClient.revokeToken(adminToken, tokenShown) }) { r ->
                    r.onSuccess {
                        minted = null
                        mintedNote = L10n.t("cu.revoked", vm.language)
                    }.onFailure { error = it.message }
                }
            }
        }
        mintedNote?.let { Text(it, color = Pdi.T2, fontSize = 10.sp) }
        Row(verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Box(Modifier.weight(1f)) {
                labeledField(L10n.t("ky.retention", vm.language), retention,
                    L10n.t("ky.retention", vm.language)) { retention = it }
            }
            SmallAction(L10n.t("co.set", vm.language)) {
                vm.call({ ApiClient.setTenantRetention(adminToken, tid,
                    retention) }) { r -> r.onFailure { error = it.message } }
            }
        }
        Text(L10n.t("cu.paperwork", vm.language), color = Pdi.Txt,
            fontSize = 14.sp, fontWeight = FontWeight.Bold)
        labeledField(L10n.t("cu.cust.name", vm.language), custName,
            L10n.t("cu.cust.name", vm.language)) { custName = it }
        labeledField(L10n.t("cu.op.name", vm.language), opName,
            L10n.t("cu.op.name", vm.language)) { opName = it }
        labeledField(L10n.t("cu.eff", vm.language), effDate,
            L10n.t("cu.eff", vm.language)) { effDate = it }
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            SmallAction(L10n.t("cu.record", vm.language)) {
                vm.call({ ApiClient.recordTenantBaa(adminToken, tid, custName,
                    opName, effDate) }) { r ->
                    r.onSuccess { baa = it }.onFailure { error = it.message }
                }
            }
            SmallAction(L10n.t("cu.onfile", vm.language)) {
                vm.call({ ApiClient.tenantBaa(adminToken, tid) }) { r ->
                    r.onSuccess { baa = it }.onFailure { error = it.message }
                }
            }
            SmallAction(L10n.t("cu.rescind", vm.language)) {
                vm.call({ ApiClient.rescindTenantBaa(adminToken, tid) }) { r ->
                    r.onSuccess { baa = null }.onFailure { error = it.message }
                }
            }
        }
        baa?.let {
            if (it.executed) {
                Text("${it.customer} \u2194 ${it.operatorName} \u00b7 ${it.date}",
                    color = Pdi.T2, fontSize = 11.sp)
            }
        }
        error?.let { Text(it, color = Pdi.Red, fontSize = 12.sp) }
    }
}

@Composable
fun GateCard(vm: VaultViewModel) {
    var ceiling by remember { mutableStateOf<GateCeilingK?>(null) }
    var channel by remember { mutableStateOf<GateChannelK?>(null) }
    var roster by remember { mutableStateOf<GateRosterK?>(null) }
    var pages by remember { mutableStateOf<List<GatePageK>>(emptyList()) }
    var rosterName by remember { mutableStateOf("") }
    var rosterRole by remember { mutableStateOf("") }
    var tz by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    fun reload() {
        vm.call({ ApiClient.gateCeiling(vm.token!!) }) { r -> ceiling = r.getOrNull() }
        vm.call({ ApiClient.gateChannel(vm.token!!) }) { r -> channel = r.getOrNull() }
        vm.call({ ApiClient.gateRoster(vm.token!!) }) { r -> roster = r.getOrNull() }
        vm.call({ ApiClient.gatePages(vm.token!!) }) { r ->
            pages = r.getOrDefault(emptyList())
        }
    }
    LaunchedEffect(Unit) { reload() }

    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("co.ceiling", vm.language), color = Pdi.Txt, fontSize = 16.sp,
            fontWeight = FontWeight.Bold)
        ceiling?.let { c ->
            Text(c.rule, color = Pdi.T2, fontSize = 11.sp)
            Text(L10n.t("co.may", vm.language) + " " + c.may.joinToString(", "),
                color = Pdi.T2, fontSize = 11.sp)
            Text(L10n.t("co.maynever", vm.language) + " "
                + c.mayNever.joinToString(", "),
                color = Pdi.T2, fontSize = 11.sp)
        }
        channel?.let { c ->
            Text(L10n.t("co.channel", vm.language) + " "
                + L10n.t(if (c.configured) "co.configured" else "co.notconfigured",
                         vm.language)
                + if (c.signed) " " + L10n.t("co.signed", vm.language) else "",
                color = Pdi.T2, fontSize = 11.sp)
        }
        Text(L10n.t("co.shift", vm.language), color = Pdi.Txt,
            fontSize = 14.sp, fontWeight = FontWeight.Bold)
        roster?.let { r ->
            if (r.roster.isEmpty()) {
                Text(L10n.t("co.noroster", vm.language), color = Pdi.T2, fontSize = 11.sp)
            }
            if (!r.anybodyOnShift) {
                Text(L10n.t("co.nobody", vm.language), color = Pdi.T2, fontSize = 11.sp)
            }
            r.roster.forEach { entry ->
                Row(Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically) {
                    Text("${entry.name} \u00b7 ${entry.role}",
                        color = Pdi.T2, fontSize = 11.sp)
                    SmallAction(L10n.t("co.remove", vm.language)) {
                        vm.call({ ApiClient.removeFromRoster(vm.token!!,
                            entry.id) }) { reload() }
                    }
                }
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            Box(Modifier.weight(1f)) {
                labeledField(L10n.t("co.name.ph", vm.language), rosterName,
                    L10n.t("co.name.ph", vm.language)) { rosterName = it }
            }
            Box(Modifier.weight(1f)) {
                labeledField(L10n.t("co.role.ph", vm.language), rosterRole,
                    L10n.t("co.role.ph", vm.language)) { rosterRole = it }
            }
            SmallAction(L10n.t("co.addroster", vm.language)) {
                if (rosterName.isNotBlank()) {
                    vm.call({ ApiClient.addToRoster(vm.token!!,
                        rosterName.trim(), rosterRole) }) {
                        rosterName = ""; reload()
                    }
                }
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            Box(Modifier.weight(1f)) {
                labeledField(L10n.t("co.tz.ph", vm.language), tz,
                    L10n.t("co.tz.ph", vm.language)) { tz = it }
            }
            SmallAction(L10n.t("co.set", vm.language)) {
                if (tz.isNotBlank()) {
                    vm.call({ ApiClient.setGateTimezone(vm.token!!, tz.trim()) }) {
                        tz = ""; reload()
                    }
                }
            }
        }
        Text(L10n.t("co.sent", vm.language), color = Pdi.Txt,
            fontSize = 14.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("co.sent.note", vm.language), color = Pdi.T2, fontSize = 11.sp)
        if (pages.isEmpty()) {
            Text(L10n.t("co.nothingpaged", vm.language), color = Pdi.T2, fontSize = 11.sp)
        }
        pages.forEach { page ->
            Row(Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically) {
                Text("${page.id} \u00b7 ${page.state}",
                    color = Pdi.T2, fontSize = 11.sp)
                if (page.state != "sent") {
                    SmallAction(L10n.t("co.retry", vm.language)) {
                        vm.call({ ApiClient.retryGatePage(vm.token!!,
                            page.id) }) { reload() }
                    }
                }
            }
        }
        error?.let { Text(it, color = Pdi.Red, fontSize = 12.sp) }
    }
}

@Composable
fun AdminCard(vm: VaultViewModel) {
    var adminToken by remember { mutableStateOf("") }
    var info by remember { mutableStateOf<KeysInfo?>(null) }
    var status by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("nadm.title", vm.language), color = Pdi.Txt, fontSize = 16.sp,
            fontWeight = FontWeight.Bold)
        Text(L10n.t("nadm.req", vm.language) + " " + L10n.t("nadm.req.more", vm.language),
            color = Pdi.T2, fontSize = 12.sp)
        labeledField(L10n.t("nadm.token", vm.language), adminToken, "…") { adminToken = it }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            SmallAction(L10n.t("nadm.versions", vm.language)) {
                error = null; status = null
                vm.call({ ApiClient.adminKeys(adminToken) }) { r ->
                    r.onSuccess { info = it }.onFailure { error = it.message }
                }
            }
            SmallAction(L10n.t("nadm.rotate", vm.language)) {
                if (info != null) {
                    error = null; status = null
                    vm.call({ ApiClient.rotateKey(adminToken) }) { r ->
                        r.onSuccess { info = it
                            status = L10n.t("nadm.rotated", vm.language) }
                         .onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("nadm.retire", vm.language)) {
                if (info != null) {
                    error = null; status = null
                    vm.call({ ApiClient.retireKeys(adminToken) }) { r ->
                        r.onSuccess { (n, k) -> info = k
                            status = "Retired $n old version(s)." }
                         .onFailure { error = it.message }
                    }
                }
            }
        }
        info?.let { k ->
            Text(L10n.t("cu.provider", vm.language) + ": " + k.provider,
                color = Pdi.T3, fontSize = 10.sp)
            k.versions.forEach { v ->
                Row(verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.size(8.dp).clip(CircleShape)
                        .background(if (v.active) Pdi.Green else Pdi.T3))
                    val vTag = "v" + v.version
                    Text(vTag, color = Pdi.Txt, fontSize = 12.sp,
                        fontWeight = FontWeight.Bold)
                    Text(if (v.active) "active" else "inactive",
                        color = if (v.active) Pdi.Green else Pdi.T3, fontSize = 10.sp)
                    Spacer(Modifier.weight(1f))
                    Text(v.createdAt ?: "", color = Pdi.T3, fontSize = 10.sp)
                }
            }
        }
        status?.let { Text(it, color = Pdi.Green, fontSize = 12.sp) }
        error?.let { Text(it, color = Pdi.Red, fontSize = 12.sp) }
    }
}

private fun masked(t: String): String =
    if (t.length > 8) t.take(6) + "…" + t.takeLast(4) else "••••"

/** Ability is not a gate: the accessibility report door. Three questions,
 *  none a diagnosis, sent with no token — reporting that the vault shut
 *  you out must not require the tenant token it may have shut you out of.
 *  The admin row reads them back with the deployment's own token. */
@Composable
fun AccessCard(vm: VaultViewModel) {
    var doing by remember { mutableStateOf("") }
    var wall by remember { mutableStateOf("") }
    var help by remember { mutableStateOf("") }
    var thanks by remember { mutableStateOf<String?>(null) }
    var reviewer by remember { mutableStateOf("") }
    var reports by remember { mutableStateOf<List<AccessReportRow>?>(null) }

    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("ns.acc", vm.language), color = Pdi.Txt, fontSize = 16.sp,
            fontWeight = FontWeight.Bold)
        Text(L10n.t("ns.acc.lead", vm.language), color = Pdi.T2, fontSize = 12.sp)
        // The per-need statement the console makes, not just its form.
        Text(L10n.t("ns.acc.needs.title", vm.language), color = Pdi.Txt,
            fontSize = 13.sp, fontWeight = FontWeight.Bold)
        listOf("blind", "deaf", "mute", "motor", "cognitive",
            "dyslexia", "motion").forEach { need ->
            Text("• " + L10n.t("ns.acc.needs.$need", vm.language),
                color = Pdi.T2, fontSize = 12.sp)
        }
        Text(L10n.t("ns.acc.needs.more", vm.language), color = Pdi.T2,
            fontSize = 12.sp, fontStyle = FontStyle.Italic)
        labeledField("", doing, L10n.t("ns.acc.doing.ph", vm.language)) { doing = it }
        labeledField("", wall, L10n.t("ns.acc.wall.ph", vm.language)) { wall = it }
        labeledField("", help, L10n.t("ns.acc.help.ph", vm.language)) { help = it }
        BrandButton(L10n.t("ns.acc.send", vm.language),
            enabled = doing.isNotBlank() && wall.isNotBlank()) {
            vm.call({ ApiClient.sendAccessReport(doing.trim(), wall.trim(),
                help.trim(), vm.language) }) {
                thanks = L10n.t("ns.acc.sent", vm.language)
                doing = ""; wall = ""; help = ""
            }
        }
        thanks?.let { Text(it, color = Pdi.Green, fontSize = 12.sp) }
        labeledField("", reviewer, L10n.t("ns.acc.token.ph", vm.language)) { reviewer = it }
        BrandButton(L10n.t("ns.acc.load", vm.language)) {
            vm.call({ ApiClient.accessReports(reviewer.trim()) }) { r ->
                reports = r.getOrNull()
            }
        }
        reports?.let { rs ->
            if (rs.isEmpty())
                Text(L10n.t("ns.acc.none", vm.language), color = Pdi.T3, fontSize = 11.sp)
            else rs.take(6).forEach { r ->
                Text(r.doing, color = Pdi.Txt, fontSize = 12.sp,
                    fontWeight = FontWeight.Bold)
                Text(r.wall, color = Pdi.T2, fontSize = 11.sp)
                r.help?.let { h -> Text(h, color = Pdi.T2, fontSize = 11.sp) }
                Text("${r.lang} · ${r.createdAt}", color = Pdi.T3, fontSize = 10.sp)
            }
        }
    }
}

@Composable
fun ImproveCard(vm: VaultViewModel) {
    val categories = listOf("idea", "improvement", "bug", "praise", "other")
    var category by remember { mutableStateOf("idea") }
    var message by remember { mutableStateOf("") }
    var rating by remember { mutableIntStateOf(0) }
    var state by remember { mutableStateOf<ImproveState?>(null) }
    var thanks by remember { mutableStateOf<String?>(null) }

    fun reload() {
        vm.call({ ApiClient.improvements(vm.token!!) }) { r -> state = r.getOrNull() }
    }
    LaunchedEffect(Unit) { reload() }

    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("nfb.title", vm.language), color = Pdi.Txt, fontSize = 16.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("nfb.sub", vm.language),
            color = Pdi.T2, fontSize = 12.sp)
        categories.chunked(3).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                row.forEach { c ->
                    FilterChip(
                        selected = category == c,
                        onClick = { category = c },
                        label = { Text(c.replaceFirstChar { it.uppercase() }, fontSize = 11.sp) },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = Pdi.BrandA,
                            selectedLabelColor = Color.White, labelColor = Pdi.T2,
                        ),
                    )
                }
            }
        }
        labeledField("", message, L10n.t("nfb.msg.ph", vm.language)) { message = it }
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(L10n.t("nfb.rating", vm.language), color = Pdi.T2, fontSize = 12.sp)
            (1..5).forEach { n ->
                Text(if (n <= rating) "★" else "☆",
                    color = if (n <= rating) Pdi.Amber else Pdi.T3, fontSize = 20.sp,
                    modifier = Modifier.clickable { rating = if (rating == n) 0 else n })
            }
        }
        BrandButton(L10n.t("nfb.send", vm.language), enabled = message.isNotBlank()) {
            vm.call({
                ApiClient.submitImprovement(vm.token!!, category, message.trim(),
                    if (rating == 0) null else rating)
            }) {
                thanks = L10n.t("fb.thanks", vm.language); message = ""; rating = 0; reload()
            }
        }
        thanks?.let { Text(it, color = Pdi.Green, fontSize = 12.sp) }
        state?.takeIf { it.total > 0 }?.let { st ->
            HorizontalDivider(color = Pdi.Line)
            Text(L10n.t("fb.sofar", vm.language).replace("{list}", categories.mapNotNull { c ->
                st.tally[c]?.takeIf { it > 0 }?.let { "$it $c" }
            }.joinToString(" · ")), color = Pdi.T3, fontSize = 10.sp)
            if (st.mine.isNotEmpty()) {
                Text(L10n.t("nfb.yours", vm.language), color = Pdi.Txt, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                st.mine.take(4).forEach { f ->
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("[${f.category}] ${f.message}", color = Pdi.T2, fontSize = 10.sp,
                            maxLines = 1, modifier = Modifier.weight(1f))
                        Text(f.status, color = Pdi.BrandA, fontSize = 10.sp)
                    }
                }
            }
        }
    }
}

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
    var provenance by remember { mutableStateOf<Map<String, RecordProvenance>>(emptyMap()) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    fun reload() { vm.call({ ApiClient.keys(vm.token!!) }) { r -> keys = r.getOrDefault(emptyList()) } }
    LaunchedEffect(Unit) { reload() }

    screenScroll {
        Text(L10n.t("tab.vault", vm.language), color = Pdi.Txt, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("nrec.sub", vm.language), color = Pdi.T2, fontSize = 13.sp)
        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            labeledField(L10n.t("nrec.key", vm.language), newKey, L10n.t("nrec.key.ph", vm.language)) { newKey = it }
            labeledField(L10n.t("nrec.value", vm.language), newValue, L10n.t("nrec.value.ph", vm.language)) { newValue = it }
            BrandButton(L10n.t("nrec.seal", vm.language), enabled = newKey.isNotBlank() && newValue.isNotBlank(), busy = busy) {
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
                Text(L10n.t("nrec.none", vm.language), color = Pdi.T2, fontSize = 13.sp)
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
                        }) { Text(if (revealed.containsKey(key)) L10n.t("nrec.hide", vm.language) else L10n.t("nrec.reveal", vm.language), color = Pdi.BrandA, fontSize = 12.sp) }
                        TextButton(onClick = {
                            if (provenance.containsKey(key)) provenance = provenance - key
                            else vm.call({ ApiClient.provenance(vm.token!!, key) }) { r ->
                                r.getOrNull()?.let { provenance = provenance + (key to it) }
                            }
                        }) { Text("ⓘ", color = Pdi.BrandA, fontSize = 12.sp) }
                        TextButton(onClick = {
                            vm.call({ ApiClient.deleteRecord(vm.token!!, key) }) { _ ->
                                revealed = revealed - key; reload()
                            }
                        }) { Text(L10n.t("nrec.delete", vm.language), color = Pdi.Red, fontSize = 12.sp) }
                    }
                    revealed[key]?.let { v ->
                        Text(v, color = Pdi.T2, fontSize = 12.sp,
                            modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(9.dp))
                                .background(Pdi.ScrBot).padding(10.dp))
                    }
                    provenance[key]?.let { p ->
                        Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(9.dp))
                            .background(Pdi.ScrBot).padding(10.dp),
                            verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            Text(L10n.t("nrec.origin", vm.language).replace("{x}", p.origin), color = Pdi.Txt, fontSize = 11.sp)
                            Text(p.cipher, color = Pdi.T2, fontSize = 10.sp)
                            Text(p.boundTo, color = Pdi.T2, fontSize = 10.sp)
                            Text(L10n.t("nrec.sealedline", vm.language).replace("{date}", p.createdAt).replace("{n}", "${p.ciphertextBytes}"),
                                color = Pdi.T3, fontSize = 10.sp)
                            Text(L10n.t("nrec.auditline", vm.language).replace("{n}", "${p.auditCount}")
                                .replace("{status}", if (p.chainIntact) L10n.t("nrec.chain.ok", vm.language) else L10n.t("nrec.chain.bad", vm.language)),
                                color = if (p.chainIntact) Pdi.Green else Pdi.Red,
                                fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        }
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
        Text(L10n.t("tab.audit", vm.language), color = Pdi.Txt, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        ProblemReportingCard(vm.language)
        Text(L10n.t("naud.desc", vm.language),
            color = Pdi.T2, fontSize = 13.sp)
        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(
                when (intact) { null -> L10n.t("naud.verifying", vm.language); true -> L10n.t("naud.intact", vm.language); else -> L10n.t("naud.broken", vm.language) },
                color = if (intact == false) Pdi.Red else Pdi.Green, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            Text(L10n.t("naud.events", vm.language).replace("{n}", "${entries?.size ?: 0}"), color = Pdi.T2, fontSize = 12.sp)
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
    var keys by remember { mutableStateOf<Map<String, List<String>>>(emptyMap()) }
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

    // Sealing hands back one key, once. Close the app and the only record of
    // what this robot has put in the vault is on the server — so a screen that
    // can seal has to be able to read the list back, or the keys are gone.
    fun showKeys(rob: Robot) {
        error = null
        vm.call({ ApiClient.robotKeys(vm.token!!, rob.id) }) { r ->
            r.onSuccess { keys = keys + (rob.id to it) }
                .onFailure { error = it.message }
        }
    }

    screenScroll {
        Text(L10n.t("tab.robots", vm.language), color = Pdi.Txt, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("nrob.sub", vm.language),
            color = Pdi.T2, fontSize = 13.sp)

        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(L10n.t("nrob.bind", vm.language), color = Pdi.Txt, fontSize = 16.sp, fontWeight = FontWeight.Bold)
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
            BrandButton(L10n.t("nrob.bind.go", vm.language), enabled = catalog.isNotEmpty(), busy = busy) {
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
                    Text(L10n.t("nrob.count", vm.language).replace("{n}", "${rob.collected}"), color = Pdi.Green, fontSize = 12.sp)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick = { seal(rob, "map", "{\"rooms\": 5}") }) {
                        Text(L10n.t("nrob.map", vm.language), color = Pdi.BrandA, fontSize = 12.sp) }
                    TextButton(onClick = { seal(rob, "snapshot", "camera still") }) {
                        Text(L10n.t("nrob.snap", vm.language), color = Pdi.BrandA, fontSize = 12.sp) }
                    TextButton(onClick = { seal(rob, "sensor_log", "steps & doors") }) {
                        Text(L10n.t("nrob.log", vm.language), color = Pdi.BrandA, fontSize = 12.sp) }
                    TextButton(onClick = {
                        vm.call({ ApiClient.unbindRobot(vm.token!!, rob.id) }) { reload() }
                    }) { Text(L10n.t("bri.unbind", vm.language), color = Pdi.Red, fontSize = 12.sp) }
                }
                TextButton(onClick = { showKeys(rob) }) {
                    Text(L10n.t("nrob.keys", vm.language), color = Pdi.BrandA, fontSize = 12.sp) }
                keys[rob.id]?.let { ks ->
                    if (ks.isEmpty()) {
                        Text(L10n.t("nrob.none", vm.language), color = Pdi.T3, fontSize = 11.sp)
                    } else {
                        ks.forEach { Text(it, color = Pdi.T2, fontSize = 11.sp) }
                        Text(L10n.t("nrob.readone", vm.language),
                            color = Pdi.T3, fontSize = 11.sp)
                    }
                }
            }
        }

        lastKey?.let { key ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(L10n.t("nrob.sealed", vm.language), color = Pdi.Txt, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                Text(key, color = Pdi.T2, fontSize = 11.sp)
                Text(L10n.t("nrob.read", vm.language), color = Pdi.T3, fontSize = 11.sp)
            }
        }
    }
}

// ---- Transfers (compliance-grade secure file transfer, both directions) ----

@Composable
fun TransfersScreen(vm: VaultViewModel) {
    var seg by remember { mutableIntStateOf(0) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)) {
        TabRow(selectedTabIndex = seg, containerColor = Pdi.Card, contentColor = Pdi.BrandA) {
            listOf("ntr.t.outbound", "ntr.t.intake", "car.title").forEachIndexed { i, t ->
                Tab(selected = seg == i, onClick = { seg = i },
                    text = { Text(L10n.t(t, vm.language), fontSize = 13.sp) })
            }
        }
        when (seg) {
            0 -> OutboundPanel(vm)
            1 -> IntakePanel(vm)
            else -> CarriersPanel(vm)
        }
    }
}

/** The console's Carriers screen, on the phone: place a custody code on a
 *  sealed thing, advance its state, read its chain, see what a scanner
 *  sees, and answer as the scanner — found and ring — plus the pairing
 *  card, because the QR on this screen is how the phone got here. */
@Composable
private fun CarriersPanel(vm: VaultViewModel) {
    var rows by remember { mutableStateOf<List<CarrierBeacon>>(emptyList()) }
    var rings by remember { mutableStateOf<List<RingK>>(emptyList()) }
    var label by remember { mutableStateOf("") }
    var disclose by remember { mutableStateOf("blind") }
    var card by remember { mutableStateOf<ScanCardK?>(null) }
    var custody by remember { mutableStateOf<CustodyChainK?>(null) }
    var transcript by remember { mutableStateOf<RingK?>(null) }
    var pair by remember { mutableStateOf<PairInfoK?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    fun reload() {
        vm.call({ ApiClient.carrierBeacons(vm.token!!) }) { r ->
            rows = r.getOrDefault(emptyList())
        }
        vm.call({ ApiClient.rings(vm.token!!) }) { r ->
            rings = r.getOrDefault(emptyList())
        }
    }
    LaunchedEffect(Unit) {
        reload()
        vm.call({ ApiClient.pairInfo() }) { r -> pair = r.getOrNull() }
    }

    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(L10n.t("car.title", vm.language), color = Pdi.Txt,
            fontSize = 22.sp, fontWeight = FontWeight.Bold)

        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(L10n.t("car.place", vm.language), color = Pdi.Txt,
                fontSize = 14.sp, fontWeight = FontWeight.Bold)
            labeledField(L10n.t("car.place", vm.language), label,
                L10n.t("car.label.ph", vm.language)) { label = it }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("blind", "contact").forEach { d ->
                    SmallAction(L10n.t("car.disclose.$d", vm.language)
                        + if (disclose == d) " ✓" else "") { disclose = d }
                }
                SmallAction(L10n.t("car.place.go", vm.language)) {
                    if (label.isNotBlank()) {
                        vm.call({ ApiClient.placeCarrierBeacon(vm.token!!,
                            label.trim(), disclose) }) { r ->
                            r.onSuccess { label = ""; reload() }
                                .onFailure { error = it.message }
                        }
                    }
                }
            }
        }

        error?.let { Text(it, color = Pdi.Red, fontSize = 12.sp) }
        if (rows.isEmpty()) {
            Text(L10n.t("car.none", vm.language), color = Pdi.T2, fontSize = 12.sp)
        }

        rows.forEach { row ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(row.label, color = Pdi.Txt, fontSize = 14.sp,
                        fontWeight = FontWeight.Bold)
                    Text("${row.refKind} · ${row.state} · ${row.disclose}"
                        + " · ×${row.scans}"
                        + if (row.active) "" else " · " + L10n.t("car.lifted", vm.language),
                        color = Pdi.T2, fontSize = 11.sp)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    SmallAction(L10n.t("car.chain", vm.language)) {
                        vm.call({ ApiClient.carrierCustody(vm.token!!, row.id) }) { r ->
                            r.onSuccess { custody = it }.onFailure { error = it.message }
                        }
                    }
                    SmallAction(L10n.t("car.sees", vm.language)) {
                        vm.call({ ApiClient.scanCard(row.id) }) { r ->
                            r.onSuccess { card = it }.onFailure { error = it.message }
                        }
                    }
                    SmallAction(L10n.t("car.refresh", vm.language)) {
                        vm.call({ ApiClient.carrierBeacon(vm.token!!, row.id) }) { reload() }
                    }
                    SmallAction(L10n.t("car.lift", vm.language)) {
                        vm.call({ ApiClient.liftCarrierBeacon(vm.token!!, row.id) }) { reload() }
                    }
                }
                // The state select, as a walk along the chain — and the
                // scanner's half, exercised from here: found and ring take
                // no bearer at all.
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    listOf("sealed", "in_transit", "delivered", "opened").forEach { st ->
                        SmallAction(if (row.state == st) "$st ✓" else st) {
                            vm.call({ ApiClient.setCarrierState(vm.token!!,
                                row.id, st) }) { reload() }
                        }
                    }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    SmallAction(L10n.t("car.ring", vm.language)) {
                        vm.call({ ApiClient.ringHolder(row.id) }) { reload() }
                    }
                    SmallAction(L10n.t("car.found", vm.language)) {
                        vm.call({ ApiClient.reportFound(row.id) }) { reload() }
                    }
                }
                Text(L10n.t("qr.addr", vm.language) + " " + ApiClient.scanQrUrl(row.id),
                    color = Pdi.T3, fontSize = 9.sp)
                Text(ApiClient.scanPageUrl(row.id), color = Pdi.T3, fontSize = 9.sp)
            }
        }

        card?.let { c ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(L10n.t("car.strangercard", vm.language), color = Pdi.Txt,
                    fontSize = 14.sp, fontWeight = FontWeight.Bold)
                Text(c.badge, color = Pdi.Txt, fontSize = 12.sp,
                    fontWeight = FontWeight.Bold)
                Text(c.note, color = Pdi.T2, fontSize = 11.sp)
                Text("${c.reference} · ${c.kind} · ${c.state} · "
                    + L10n.t(if (c.underCustody) "car.custody.yes"
                             else "car.custody.no", vm.language),
                    color = Pdi.T2, fontSize = 11.sp)
                Text(L10n.t("car.contents", vm.language) + " "
                    + L10n.t("car.contents.no", vm.language) + " "
                    + L10n.t("car.contents.never", vm.language),
                    color = Pdi.T3, fontSize = 10.sp)
            }
        }

        custody?.let { ch ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(L10n.t("car.chain", vm.language), color = Pdi.Txt,
                    fontSize = 14.sp, fontWeight = FontWeight.Bold)
                Text(L10n.t("car.auditchain", vm.language) + " "
                    + L10n.t(if (ch.intact) "car.verifies" else "car.notverify",
                             vm.language),
                    color = Pdi.T2, fontSize = 11.sp)
                ch.events.forEach { Text(it, color = Pdi.T2, fontSize = 11.sp) }
            }
        }

        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(L10n.t("car.rang", vm.language), color = Pdi.Txt,
                fontSize = 14.sp, fontWeight = FontWeight.Bold)
            if (rings.isEmpty()) {
                Text(L10n.t("car.norings", vm.language), color = Pdi.T2,
                    fontSize = 11.sp)
            }
            rings.forEach { r ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically) {
                    Text("${r.kind} · ${r.state} · ${r.createdAt}",
                        color = Pdi.T2, fontSize = 11.sp)
                    SmallAction(L10n.t("car.transcript", vm.language)) {
                        vm.call({ ApiClient.ringTranscript(vm.token!!, r.id) }) { t ->
                            t.onSuccess { transcript = it }
                                .onFailure { error = it.message }
                        }
                    }
                }
            }
            transcript?.let {
                Text("${it.kind} · ${it.note} · ${it.outcome}",
                    color = Pdi.T3, fontSize = 10.sp)
            }
        }

        // The pairing card: the card's own words, straight from the wire.
        pair?.let { p ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                p.how.forEach {
                    Text(it, color = Pdi.T2, fontSize = 11.sp,
                        fontWeight = FontWeight.Bold)
                }
                Text(p.consoleUrl, color = Pdi.Txt, fontSize = 11.sp)
                Text(p.note, color = Pdi.T3, fontSize = 10.sp)
                Text(L10n.t("qr.addr", vm.language) + " " + ApiClient.pairQrUrl(),
                    color = Pdi.T3, fontSize = 10.sp)
            }
        }
    }
}

@Composable
private fun OutboundPanel(vm: VaultViewModel) {
    var programs by remember { mutableStateOf<List<ComplianceProgram>>(emptyList()) }
    var selected by remember { mutableStateOf(setOf("hipaa")) }
    var recipient by remember { mutableStateOf("") }
    var filename by remember { mutableStateOf("") }
    var content by remember { mutableStateOf("") }
    var transfers by remember { mutableStateOf<List<Transfer>>(emptyList()) }
    var minted by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var linkOk by remember { mutableStateOf<String?>(null) }
    var chainLine by remember { mutableStateOf<String?>(null) }
    var receivedLine by remember { mutableStateOf<String?>(null) }

    fun reload() { vm.call({ ApiClient.transfers(vm.token!!) }) { r -> transfers = r.getOrDefault(emptyList()) } }
    LaunchedEffect(Unit) {
        vm.call({ ApiClient.compliancePrograms(vm.token!!) }) { r -> programs = r.getOrDefault(emptyList()) }
        reload()
    }

    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(L10n.t("tab.transfers", vm.language), color = Pdi.Txt, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("nfil.sub", vm.language),
            color = Pdi.T2, fontSize = 13.sp)

        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            labeledField(L10n.t("nfil.recipient", vm.language), recipient, L10n.t("nfil.recipient.ph", vm.language)) { recipient = it }
            labeledField(L10n.t("nfil.filename", vm.language), filename, L10n.t("nfil.filename.ph", vm.language)) { filename = it }
            labeledField(L10n.t("nfil.content", vm.language), content, L10n.t("nfil.content.ph", vm.language)) { content = it }
            Text(L10n.t("nfil.programs", vm.language), color = Pdi.T2, fontSize = 12.sp)
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
            BrandButton(L10n.t("nfil.seal", vm.language),
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
                Text(L10n.t("nfil.token.once", vm.language), color = Pdi.Amber, fontSize = 15.sp,
                    fontWeight = FontWeight.Bold)
                Text(tok, color = Pdi.Txt, fontSize = 11.sp)
                Text(L10n.t("nfil.token.hand", vm.language),
                    color = Pdi.T2, fontSize = 11.sp)
            }
        }

        chainLine?.let { Text(it, color = Pdi.T2, fontSize = 11.sp) }
        receivedLine?.let { Text(it, color = Pdi.T2, fontSize = 11.sp) }
        transfers.forEach { t ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(t.filename, color = Pdi.Txt, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text(t.status.replaceFirstChar { it.uppercase() },
                        color = if (t.status == "revoked") Pdi.Red else Pdi.Green, fontSize = 12.sp)
                }
                val line = "\u2192 " + t.recipient + " \u00b7 " +
                    t.programs.joinToString(" ") { it.uppercase() }
                Text(line,
                    color = Pdi.T2, fontSize = 12.sp)
                t.expiresAt?.let { Text(L10n.t("ntr.retained", vm.language).replace("{date}", it), color = Pdi.T3, fontSize = 11.sp) }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically) {
                    SmallAction(L10n.t("car.refresh", vm.language)) {
                        vm.call({ ApiClient.transferOne(vm.token!!, t.id) }) { reload() }
                    }
                    SmallAction(L10n.t("car.chain", vm.language)) {
                        vm.call({ ApiClient.transferCustody(vm.token!!, t.id) }) { r ->
                            r.onSuccess { c ->
                                chainLine = L10n.t(
                                    if (c.intact) "car.verifies" else "car.notverify",
                                    vm.language) + " \u00b7 ${c.events.size}"
                            }
                        }
                    }
                    // The recipient's act, with the one-shot token this
                    // screen just minted.
                    if (minted != null) {
                        SmallAction(L10n.t("exc.asrecipient", vm.language)) {
                            vm.call({ ApiClient.receiveTransfer(t.id, minted!!) }) { r ->
                                r.onSuccess { receivedLine = it }
                                    .onFailure { error = it.message }
                            }
                        }
                    }
                    // Resolve the recipient's page before the link goes into
                    // an email — a misconfigured public base is otherwise
                    // discovered by the recipient, who has nobody to ask.
                    SmallAction(L10n.t("ntr.reciplink", vm.language)) {
                        vm.call({ ApiClient.checkRecipientPage(t.id) }) { r ->
                            if (r.getOrDefault(false)) linkOk = t.id
                        }
                    }
                    if (linkOk == t.id) {
                        Text(L10n.t("car.verifies", vm.language),
                            color = Pdi.Green, fontSize = 11.sp)
                    }
                    if (t.status != "revoked") {
                        TextButton(onClick = {
                            vm.call({ ApiClient.revokeTransfer(vm.token!!, t.id) }) { reload() }
                        }) { Text(L10n.t("ntr.revoke", vm.language), color = Pdi.Red, fontSize = 12.sp) }
                    }
                }
            }
        }
    }
}

// ---- Intake (request a file in; the sender submits with a one-shot token) ----

@Composable
private fun IntakePanel(vm: VaultViewModel) {
    var programs by remember { mutableStateOf<List<ComplianceProgram>>(emptyList()) }
    var selected by remember { mutableStateOf(setOf("hipaa")) }
    var fromParty by remember { mutableStateOf("") }
    var purpose by remember { mutableStateOf("") }
    var intakes by remember { mutableStateOf<List<Intake>>(emptyList()) }
    var intakeChain by remember { mutableStateOf<String?>(null) }
    var minted by remember { mutableStateOf<String?>(null) }
    var received by remember { mutableStateOf<Map<String, IntakeFile>>(emptyMap()) }
    var senderToken by remember { mutableStateOf("") }
    var senderFile by remember { mutableStateOf("") }
    var senderContent by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    fun reload() { vm.call({ ApiClient.intakes(vm.token!!) }) { r -> intakes = r.getOrDefault(emptyList()) } }
    LaunchedEffect(Unit) {
        vm.call({ ApiClient.compliancePrograms(vm.token!!) }) { r -> programs = r.getOrDefault(emptyList()) }
        reload()
    }

    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(L10n.t("ntr.intake", vm.language), color = Pdi.Txt, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("ntr.intake.sub", vm.language),
            color = Pdi.T2, fontSize = 13.sp)

        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            labeledField(L10n.t("nreq.from", vm.language), fromParty, L10n.t("nreq.from.ph", vm.language)) { fromParty = it }
            labeledField(L10n.t("nreq.purpose", vm.language), purpose, L10n.t("nreq.purpose.ph", vm.language)) { purpose = it }
            Text(L10n.t("nfil.programs", vm.language), color = Pdi.T2, fontSize = 12.sp)
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
            BrandButton(L10n.t("nreq.go", vm.language),
                enabled = fromParty.isNotBlank() && selected.isNotEmpty(), busy = busy) {
                busy = true; error = null
                vm.call({ ApiClient.createIntake(vm.token!!, fromParty, purpose,
                                                  selected.toList()) }) { r ->
                    busy = false
                    r.onSuccess { minted = it.submitToken; fromParty = ""; purpose = "" }
                     .onFailure { error = it.message }
                    reload()
                }
            }
        }
        error?.let { Text(it, color = Pdi.Red, fontSize = 13.sp) }

        minted?.let { tok ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(L10n.t("nint.token.once", vm.language), color = Pdi.Amber, fontSize = 15.sp,
                    fontWeight = FontWeight.Bold)
                Text(tok, color = Pdi.Txt, fontSize = 11.sp)
                Text(L10n.t("nint.token.send", vm.language),
                    color = Pdi.T2, fontSize = 11.sp)
            }
        }

        intakeChain?.let { Text(it, color = Pdi.T2, fontSize = 11.sp) }
        intakes.forEach { i ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(i.fromParty, color = Pdi.Txt, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text(i.status.replaceFirstChar { it.uppercase() },
                        color = if (i.status == "submitted") Pdi.Green else Pdi.T2, fontSize = 12.sp)
                }
                i.purpose?.let { Text(it, color = Pdi.T2, fontSize = 12.sp) }
                Text(i.programs.joinToString(" ") { it.uppercase() }, color = Pdi.T3, fontSize = 11.sp)
                if (i.status == "submitted") {
                    TextButton(onClick = {
                        vm.call({ ApiClient.intakeFile(vm.token!!, i.id) }) { r ->
                            r.getOrNull()?.let { f -> received = received + (i.id to f) }
                        }
                    }) { Text(L10n.t("ntr.read", vm.language), color = Pdi.BrandA, fontSize = 12.sp) }
                    received[i.id]?.let { f ->
                        val fileLine = (f.filename ?: "file") + ": " + (f.content ?: "")
                        Text(fileLine,
                            color = Pdi.T2, fontSize = 11.sp,
                            modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(9.dp))
                                .background(Pdi.ScrBot).padding(8.dp))
                    }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    SmallAction(L10n.t("car.refresh", vm.language)) {
                        vm.call({ ApiClient.intakeOne(vm.token!!, i.id) }) { reload() }
                    }
                    SmallAction(L10n.t("car.chain", vm.language)) {
                        vm.call({ ApiClient.intakeCustody(vm.token!!, i.id) }) { r ->
                            r.onSuccess { c ->
                                intakeChain = L10n.t(
                                    if (c.intact) "car.verifies" else "car.notverify",
                                    vm.language) + " \u00b7 ${c.events.size}"
                            }
                        }
                    }
                }
                if (i.status == "open") {
                    TextButton(onClick = {
                        vm.call({ ApiClient.closeIntake(vm.token!!, i.id) }) { reload() }
                    }) { Text(L10n.t("nreq.close", vm.language), color = Pdi.Red, fontSize = 12.sp) }
                }
            }
        }

        // The counterparty's side, for exercising the loop on-device.
        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(L10n.t("ntr.as.sender", vm.language), color = Pdi.Txt, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            Text(L10n.t("ntr.answer.sub", vm.language),
                color = Pdi.T2, fontSize = 12.sp)
            labeledField(L10n.t("nint.token", vm.language), senderToken, L10n.t("nint.token.ph", vm.language)) { senderToken = it }
            labeledField(L10n.t("nfil.filename", vm.language), senderFile, L10n.t("nint.filename.ph", vm.language)) { senderFile = it }
            labeledField(L10n.t("nfil.content", vm.language), senderContent, L10n.t("nint.content.ph", vm.language)) { senderContent = it }
            BrandButton(L10n.t("nint.go", vm.language),
                enabled = senderToken.isNotBlank() && senderFile.isNotBlank()
                          && senderContent.isNotBlank()) {
                val target = intakes.lastOrNull { it.status == "open" }
                if (target == null) { error = "no open intake to submit into" }
                else {
                    error = null
                    vm.call({ ApiClient.submitIntake(target.id, senderToken,
                                                      senderFile, senderContent) }) { r ->
                        r.onSuccess { senderToken = ""; senderFile = ""; senderContent = "" }
                         .onFailure { error = it.message }
                        reload()
                    }
                }
            }
        }
    }
}

// ---- Sources (Robots · Connectors behind one tab) ----

@Composable
fun SourcesScreen(vm: VaultViewModel) {
    var seg by remember { mutableIntStateOf(0) }
    Column(Modifier.fillMaxSize()) {
        TabRow(selectedTabIndex = seg, containerColor = Pdi.Card, contentColor = Pdi.BrandA) {
            listOf("tab.robots", "tab.connectors").forEachIndexed { i, t ->
                Tab(selected = seg == i, onClick = { seg = i },
                    text = { Text(L10n.t(t, vm.language), fontSize = 13.sp) })
            }
        }
        Box(Modifier.weight(1f)) {
            if (seg == 0) RobotsScreen(vm) else ConnectorsPanel(vm)
        }
    }
}

// ---- Connectors (social-platform data sources; ingest is audited) ----

@Composable
private fun ConnectorsPanel(vm: VaultViewModel) {
    val platforms = listOf("instagram", "x", "tiktok", "facebook", "linkedin",
        "youtube", "whatsapp", "discord", "twitch", "pinterest", "snapchat", "mastodon")
    var platform by remember { mutableStateOf("instagram") }
    var handle by remember { mutableStateOf("") }
    var conns by remember { mutableStateOf<List<SocialConn>>(emptyList()) }
    var status by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var catalogLine by remember { mutableStateOf<String?>(null) }
    var beaconLine by remember { mutableStateOf<String?>(null) }

    fun reload() { vm.call({ ApiClient.connectors(vm.token!!) }) { r -> conns = r.getOrDefault(emptyList()) } }
    LaunchedEffect(Unit) {
        reload()
        vm.call({ ApiClient.connectorCatalog() }) { r ->
            catalogLine = r.getOrNull()?.toString()
        }
    }

    fun connect(direction: String) {
        error = null; status = null
        vm.call({ ApiClient.createConnector(vm.token!!, platform, direction, handle) }) { r ->
            r.onSuccess { handle = "" }.onFailure { error = it.message }
            reload()
        }
    }

    screenScroll {
        Text(L10n.t("tab.connectors", vm.language), color = Pdi.Txt, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text(L10n.t("ncon.sub", vm.language),
            color = Pdi.T2, fontSize = 13.sp)

        Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            platforms.chunked(4).forEach { row ->
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    row.forEach { pl ->
                        FilterChip(
                            selected = platform == pl, onClick = { platform = pl },
                            label = { Text(pl, fontSize = 10.sp) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = Pdi.BrandA,
                                selectedLabelColor = Color.White, labelColor = Pdi.T2,
                            ),
                        )
                    }
                }
            }
            labeledField(L10n.t("nacc.handle", vm.language), handle, L10n.t("nacc.handle.ph", vm.language)) { handle = it }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                TextButton(onClick = { connect("collect") }) {
                    Text(L10n.t("ncon.collect", vm.language), color = Pdi.BrandA, fontSize = 13.sp) }
                TextButton(onClick = { connect("publish") }) {
                    Text(L10n.t("ncon.publish", vm.language), color = Pdi.BrandA, fontSize = 13.sp) }
            }
        }
        error?.let { Text(it, color = Pdi.Red, fontSize = 13.sp) }
        status?.let { Text(it, color = Pdi.Green, fontSize = 12.sp) }
        catalogLine?.let {
            Text(L10n.t("bri.pick", vm.language) + " " + it,
                color = Pdi.T2, fontSize = 11.sp)
        }
        beaconLine?.let { Text(it, color = Pdi.T2, fontSize = 10.sp) }

        conns.forEach { c ->
            Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("${c.platform.replaceFirstChar { it.uppercase() }} · ${c.direction}",
                        color = Pdi.Txt, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    c.handle?.let { Text("@$it", color = Pdi.T3, fontSize = 12.sp) }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (c.direction == "collect") {
                        TextButton(onClick = {
                            vm.call({ ApiClient.connectorIngest(vm.token!!, c.id,
                                "sample post from ${c.platform}") }) { r ->
                                r.onSuccess { status = "sealed one item from ${c.platform}" }
                                 .onFailure { error = it.message }
                            }
                        }) { Text(L10n.t("ncon.ingest", vm.language), color = Pdi.BrandA, fontSize = 12.sp) }
                        val h = c.handle
                        if (h != null && h.isNotEmpty())
                            TextButton(onClick = {
                                vm.call({ ApiClient.connectorScrape(vm.token!!, c.id) }) { r ->
                                    r.onSuccess { status = "fetched ${c.platform} — the page is sealed in the vault" }
                                     .onFailure { error = it.message }
                                }
                            }) { Text(L10n.t("ncon.scrape", vm.language), color = Pdi.BrandA, fontSize = 12.sp) }
                    }
                    else
                        TextButton(onClick = {
                            vm.call({ ApiClient.connectorPublish(vm.token!!, c.id,
                                "An update from the vault.") }) { r ->
                                r.onSuccess { status = "published to ${c.platform}" }
                                 .onFailure { error = it.message }
                            }
                        }) { Text(L10n.t("ncon.update", vm.language), color = Pdi.BrandA, fontSize = 12.sp) }
                    // Each connection's own code: the beacon's words plus
                    // the address of the image a browser fetches.
                    TextButton(onClick = {
                        vm.call({ ApiClient.connectorBeacon(vm.token!!, c.id) }) { r ->
                            r.onSuccess { body ->
                                beaconLine = L10n.t("qr.addr", vm.language) + " " +
                                    ApiClient.connectorQrUrl(c.id) + " \u00b7 " +
                                    body.take(120)
                            }.onFailure { error = it.message }
                        }
                    }) { Text(L10n.t("bri.itscode", vm.language), color = Pdi.BrandA, fontSize = 12.sp) }
                    TextButton(onClick = {
                        vm.call({ ApiClient.revokeConnector(vm.token!!, c.id) }) { reload() }
                    }) { Text(L10n.t("ncon.disconnect", vm.language), color = Pdi.Red, fontSize = 12.sp) }
                }
            }
        }
    }
}

/**
 * The notice that has to be answered before anything leaves the device, and
 * the switch that turns it off afterwards.
 *
 * The sending half landed last round and answers AWAITING_NOTICE on every
 * launch, because there was no surface to answer it on. Safe to be wrong in
 * that direction, and still wrong: a mechanism nobody can reach is a
 * mechanism nobody chose.
 *
 * Two rules this card keeps:
 *
 *  * **Show the report, do not describe it.** A card that says "we collect
 *    anonymous diagnostics" asks somebody to take our word for it.
 *    `Problems.report` is the same function the sender posts, so what is on
 *    screen is the payload. A preview that could drift from the message would
 *    be worse than none, because it would look like a promise.
 *  * **No pre-ticked answer.** Neither button is the emphasised one. A dialog
 *    with a bright Yes and a grey No has made the choice already.
 */
@Composable
fun ProblemReportingCard(lang: String) {
    var answered by remember { mutableStateOf(Problems.noticeAnswered()) }
    var sending by remember { mutableStateOf(Problems.sendingEnabled()) }
    var showing by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    var readerKey by remember { mutableStateOf("") }
    var serverRows by remember {
        mutableStateOf<List<ApiClient.ProblemRow>?>(null) }
    val owed = remember(showing, answered, sending) {
        val arr = Problems.report().optJSONArray("problems")
        (0 until (arr?.length() ?: 0)).mapNotNull { arr?.optJSONObject(it) }
    }

    Card(colors = CardDefaults.cardColors(containerColor = Pdi.Card)) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(L10n.t("prb.title", lang), style = MaterialTheme.typography.titleSmall)

            if (Problems.collectorUrl().isEmpty()) {
                // Not a failure and not a thing to hide: this build has no
                // address compiled in, so there is nothing to consent to.
                Text(L10n.t("prb.nowhere", lang),
                     style = MaterialTheme.typography.bodySmall)
            } else if (!answered) {
                Text(L10n.t("prb.can", lang),
                     style = MaterialTheme.typography.bodySmall)
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    OutlinedButton(onClick = {
                        Problems.answerNotice(true); answered = true; sending = true
                        // The first moment a send is permitted. Doing it now
                        // rather than at the next launch means the person who
                        // just agreed watches the buffer drain, instead of
                        // being told something happened later.
                        scope.launch(Dispatchers.IO) { Problems.send() }
                    }) { Text(L10n.t("prb.send", lang)) }
                    OutlinedButton(onClick = {
                        Problems.answerNotice(false); answered = true; sending = false
                    }) { Text(L10n.t("prb.donot", lang)) }
                }
            } else {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(L10n.t("prb.toggle", lang), Modifier.weight(1f),
                         style = MaterialTheme.typography.bodyMedium)
                    Switch(checked = sending, onCheckedChange = {
                        sending = it; Problems.setSending(it)
                    })
                }
            }

            TextButton(onClick = { showing = !showing }) {
                Text(if (showing) L10n.t("prb.hide", lang)
                     else L10n.t("prb.show", lang))
            }
            if (showing) {
                if (owed.isEmpty()) {
                    Text(L10n.t("prb.owed.none", lang),
                         style = MaterialTheme.typography.bodySmall)
                } else {
                    owed.forEach { r ->
                        val problemLine = r.optString("op") + " \u2192 " +
                            r.optInt("status") + "  \u00d7" + r.optInt("count") +
                            "  " + r.optString("day")
                        Text(problemLine,
                             style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
            // The other end of the wire: what has reached this deployment's
            // own backend, from every client of it. Reading needs the
            // problems key (or a caller on the backend's machine); a refusal
            // is rendered verbatim.
            HorizontalDivider()
            Text(L10n.t("prob.server", lang),
                 style = MaterialTheme.typography.titleSmall)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically) {
                OutlinedTextField(value = readerKey,
                    onValueChange = { readerKey = it },
                    placeholder = { Text(L10n.t("prob.key.ph", lang)) },
                    modifier = Modifier.weight(1f), singleLine = true)
                OutlinedButton(onClick = {
                    scope.launch(Dispatchers.IO) {
                        serverRows = try { ApiClient.problemRows(readerKey) }
                                     catch (e: Exception) { emptyList() }
                    }
                }) { Text(L10n.t("prob.fetch", lang)) }
            }
            serverRows?.let { rows ->
                if (rows.isEmpty()) {
                    Text(L10n.t("prob.none", lang),
                         style = MaterialTheme.typography.bodySmall)
                } else rows.forEach { r ->
                    Text("${r.op}  ${r.statusCode}  ×${r.count}  " +
                         "${r.source} ${r.appVersion} · ${r.platform} · ${r.day}",
                         style = MaterialTheme.typography.bodySmall)
                }
            }

        }
    }
}

/** The console's guide, from the phone: the walkthrough stepped through, a
 *  question asked of the assistant, one of PDI's own notes translated. All
 *  of it describes the console rather than anybody's data. */
@Composable
fun GuideCard(vm: VaultViewModel) {
    var outlineLine by remember { mutableStateOf<String?>(null) }
    var progress by remember { mutableStateOf<ApiClient.GuideWhereK?>(null) }
    var stepLine by remember { mutableStateOf<String?>(null) }
    var question by remember { mutableStateOf("") }
    var answerLine by remember { mutableStateOf<String?>(null) }
    var noteText by remember { mutableStateOf("") }
    var trLine by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    val learner = "phone-operator"

    LaunchedEffect(Unit) {
        vm.call({ ApiClient.guideOutline() }) { r ->
            r.onSuccess {
                outlineLine = "$it " + L10n.t("gd.steps", vm.language)
            }
        }
    }
    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("gd.guide", vm.language), color = Pdi.Txt,
            fontSize = 16.sp, fontWeight = FontWeight.Bold)
        outlineLine?.let { Text(it, color = Pdi.T2, fontSize = 10.sp) }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            SmallAction(L10n.t("gd.start", vm.language)) {
                vm.call({ ApiClient.guideStart(learner) }) { r ->
                    r.onSuccess { progress = it }.onFailure { error = it.message }
                }
            }
            SmallAction(L10n.t("gd.done", vm.language)) {
                val key = progress?.step?.key
                if (key != null) {
                    vm.call({ ApiClient.guideDone(learner, key) }) { r ->
                        r.onSuccess { progress = it }
                            .onFailure { error = it.message }
                    }
                } else {
                    vm.call({ ApiClient.guideProgress(learner) }) { r ->
                        r.onSuccess { progress = it }
                            .onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("gd.step", vm.language)) {
                progress?.step?.key?.let { k ->
                    vm.call({ ApiClient.guideStep(k) }) { r ->
                        r.onSuccess { stepLine = it.title + " \u2014 " + it.said }
                            .onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("gd.thisscreen", vm.language)) {
                vm.call({ ApiClient.guideForScreen(1) }) { r ->
                    r.onSuccess { stepLine = it.title + " \u2014 " + it.said }
                        .onFailure { error = it.message }
                }
            }
        }
        progress?.let { p ->
            val line = L10n.t("gd.progress", vm.language)
                .replace("{done}", p.done.toString())
                .replace("{total}", p.total.toString())
            Text(line + " \u00b7 " + (p.step?.title ?: p.note),
                color = Pdi.T2, fontSize = 10.sp)
        }
        stepLine?.let { Text(it, color = Pdi.T2, fontSize = 10.sp) }
        Row(verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Box(Modifier.weight(1f)) {
                labeledField(L10n.t("gd.q.ph", vm.language), question,
                    L10n.t("gd.q.ph", vm.language)) { question = it }
            }
            SmallAction(L10n.t("gd.ask.go", vm.language)) {
                if (question.isNotBlank()) {
                    vm.call({ ApiClient.consoleAsk(question.trim()) }) { r ->
                        r.onSuccess { answerLine = it }
                            .onFailure { error = it.message }
                    }
                }
            }
        }
        answerLine?.let { Text(it, color = Pdi.T2, fontSize = 10.sp) }
        Row(verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Box(Modifier.weight(1f)) {
                labeledField(L10n.t("gd.text.ph", vm.language), noteText,
                    L10n.t("gd.text.ph", vm.language)) { noteText = it }
            }
            SmallAction(L10n.t("gd.translate", vm.language)) {
                if (noteText.isNotBlank()) {
                    vm.call({ ApiClient.translate(vm.token!!, noteText) }) { r ->
                        r.onSuccess {
                            trLine = L10n.t("gd.engine", vm.language) + " " + it
                        }.onFailure { error = it.message }
                    }
                }
            }
        }
        trLine?.let { Text(it, color = Pdi.T2, fontSize = 10.sp) }
        error?.let { Text(it, color = Pdi.Red, fontSize = 11.sp) }
    }
}

/** The pane in the corner, from the phone: its public vocabulary, this
 *  tenant's arrangement, and one face as the pane would draw it. */
@Composable
fun DockCard(vm: VaultViewModel) {
    var vocabLine by remember { mutableStateOf<String?>(null) }
    var tid by remember { mutableStateOf("") }
    var current by remember { mutableStateOf<ApiClient.DockSettingsK?>(null) }
    var faceLine by remember { mutableStateOf<String?>(null) }
    var whereLine by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        vm.call({ ApiClient.dockVocabulary() }) { r ->
            r.onSuccess { vocabLine = it }
        }
    }
    Column(Modifier.card(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(L10n.t("gd.corner", vm.language), color = Pdi.Txt,
            fontSize = 16.sp, fontWeight = FontWeight.Bold)
        vocabLine?.let { Text(it, color = Pdi.T2, fontSize = 10.sp) }
        labeledField(L10n.t("adm.tenant.ph", vm.language), tid,
            L10n.t("adm.tenant.ph", vm.language)) { tid = it }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            SmallAction(L10n.t("gd.open", vm.language)) {
                if (tid.isNotBlank()) {
                    vm.call({ ApiClient.dockSettings(vm.token!!, tid.trim()) }) { r ->
                        r.onSuccess { current = it }
                            .onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("gd.othercorner", vm.language)) {
                if (tid.isNotBlank()) {
                    val corner = if (current?.corner == "bottom_right")
                        "bottom_left" else "bottom_right"
                    vm.call({ ApiClient.dockConfigure(vm.token!!, tid.trim(),
                        corner) }) { r ->
                        r.onSuccess { current = it }
                            .onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("gd.showing", vm.language)) {
                val face = current?.face
                if (tid.isNotBlank() && face != null) {
                    vm.call({ ApiClient.dockFace(vm.token!!, tid.trim(),
                        face) }) { r ->
                        r.onSuccess { faceLine = it }
                            .onFailure { error = it.message }
                    }
                }
            }
            SmallAction(L10n.t("gd.use", vm.language)) {
                vm.call({ ApiClient.dockWhere(current?.face ?: "helper") }) { r ->
                    r.onSuccess { whereLine = it }
                        .onFailure { error = it.message }
                }
            }
        }
        current?.let {
            Text(it.corner + " \u00b7 " + it.state + " \u00b7 " + it.face,
                color = Pdi.T2, fontSize = 10.sp)
        }
        faceLine?.let { Text(it, color = Pdi.T2, fontSize = 10.sp) }
        whereLine?.let { Text(it, color = Pdi.T2, fontSize = 10.sp) }
        error?.let { Text(it, color = Pdi.Red, fontSize = 11.sp) }
    }
}

/**
 * The version handshake, made visible on the phone.
 *
 * A stale backend from an older install answers `/health` perfectly well
 * and then serves an older API, so the app looks alive while every newer
 * screen answers "Not Found" with no explanation. The console has said so
 * since the mismatch first cost somebody an evening; this shell could be
 * pointed at the same stale address — `ApiClient.base` has a setter for
 * exactly that — and said nothing at all.
 *
 *     asked     is the backend reachable
 *     mattered  is it the backend this build was written against
 *
 * Reachability was the only question any shell asked. `/health` has carried
 * the answer to the second one the whole time, and `health()` above reads
 * the same response and keeps only the status.
 *
 * Dismissible, because somebody who knows and is working anyway should not
 * read it on every screen; and per-launch rather than remembered, because
 * the condition is true until the address or the backend changes, and a
 * permanently silenced warning about a broken deployment is worse than
 * none.
 */
@Composable
fun VersionGuardBar(language: String) {
    var backend by remember { mutableStateOf<String?>(null) }
    var dismissed by remember { mutableStateOf(false) }
    val mine = com.pdi.vault.BuildConfig.VERSION_NAME

    LaunchedEffect(Unit) {
        // An unreachable backend is the connection panel's story, not this
        // one: a version guard that also complained about being offline
        // would cry wolf every time a phone changed network.
        backend = try {
            // A backend too old to carry the field is the loudest case
            // there is, so it gets a name rather than reading as agreement.
            ApiClient.backendVersion().ifBlank { L10n.t("vg.ancient", language) }
        } catch (_: Exception) { null }
    }

    val seen = backend
    if (dismissed || seen == null || seen == mine) return

    Card(
        colors = CardDefaults.cardColors(containerColor = Pdi.Card),
        modifier = Modifier.fillMaxWidth().padding(12.dp),
    ) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.Top) {
            Text("⚠", color = Pdi.Amber, fontSize = 18.sp)
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text(L10n.t("vg.title", language), color = Pdi.Txt,
                     fontWeight = FontWeight.Bold, fontSize = 14.sp)
                Spacer(Modifier.height(4.dp))
                Text(String.format(L10n.t("vg.body", language),
                                   mine, ApiClient.base, seen),
                     color = Pdi.T2, fontSize = 12.sp)
                Spacer(Modifier.height(4.dp))
                Text(L10n.t("vg.fix", language), color = Pdi.T3, fontSize = 11.sp)
            }
            TextButton(onClick = { dismissed = true }) {
                Text(L10n.t("vg.dismiss", language), color = Pdi.T2, fontSize = 12.sp)
            }
        }
    }
}
