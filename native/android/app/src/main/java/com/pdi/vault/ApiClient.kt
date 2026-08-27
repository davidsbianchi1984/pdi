package com.pdi.vault

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

// MARK: wire models (mirror pdi/api.py)

data class VaultRecord(val key: String, val value: String, val updatedAt: String?)
data class RecordProvenance(val origin: String, val cipher: String, val boundTo: String,
                            val createdAt: String, val ciphertextBytes: Int,
                            val auditCount: Int, val chainIntact: Boolean)
data class LanguageInfo(val code: String, val label: String, val notesTranslated: Boolean)
data class AcceptanceCheck(val check: String, val says: String,
                          val passed: Boolean, val detail: String)

data class AcceptanceReport(val at: String, val passing: Int, val of: Int,
                            val clean: Boolean,
                            val checks: List<AcceptanceCheck>)

data class AuditEntry(val seq: Int, val action: String, val ref: String?, val at: String, val category: String?)
data class RobotSpec(val model: String, val label: String, val maker: String)
data class Robot(val id: String, val model: String, val name: String, val status: String?, val collected: Int)
data class IngestResult(val sealed: Boolean, val key: String)
data class ComplianceProgram(val key: String, val label: String)
data class HostingModeK(val id: String, val title: String,
                        val price: String, val means: String,
                        val freeBecause: String, val we: String,
                        val you: String)
data class BequestK(val id: String, val grantee: String,
                    val condition: String, val prefixes: List<String>,
                    val activated: Boolean, val revoked: Boolean,
                    val grantToken: String)
data class TenantMadeK(val id: String, val name: String, val token: String)
data class BaaK(val executed: Boolean, val customer: String,
                val operatorName: String, val date: String)
data class GateCeilingK(val rule: String, val may: List<String>,
                        val mayNever: List<String>)
data class GateChannelK(val configured: Boolean, val signed: Boolean)
data class RosterEntryK(val id: String, val name: String, val role: String)
data class GateRosterK(val configured: Boolean,
                       val roster: List<RosterEntryK>,
                       val anybodyOnShift: Boolean)
data class GatePageK(val id: String, val state: String)
data class CarrierBeacon(val id: String, val refKind: String,
                         val label: String, val disclose: String,
                         val state: String, val scans: Int, val active: Boolean)
data class ScanCardK(val reference: String, val kind: String, val state: String,
                     val underCustody: Boolean, val badge: String,
                     val note: String)
data class CustodyChainK(val intact: Boolean, val events: List<String>)
data class RingK(val id: String, val kind: String, val note: String,
                 val state: String, val outcome: String, val createdAt: String)
data class PairInfoK(val consoleUrl: String, val how: List<String>,
                     val note: String)
data class Transfer(val id: String, val recipient: String, val filename: String,
                    val status: String, val programs: List<String>,
                    val expiresAt: String?, val receiveToken: String?)
data class Intake(val id: String, val fromParty: String, val purpose: String?,
                  val status: String, val programs: List<String>,
                  val filename: String?, val submitToken: String?)
data class IntakeFile(val filename: String?, val content: String?)
data class SocialConn(val id: String, val platform: String, val direction: String,
                      val handle: String?, val status: String?)

// The resident intelligence's wire shapes (pdi/resident.py). `leavesHost`
// travels with every tool and step on purpose: a person deciding whether
// to run a plan should not have to read Python to learn which steps go
// outside.
data class ResidentTool(val name: String, val means: String, val leavesHost: Boolean)
data class ResidentPosture(val means: String, val hostingMode: String,
                           val localModel: String?, val embedder: String,
                           val tools: List<ResidentTool>, val privacy: String)
data class ResidentStep(val position: Int, val title: String, val tool: String,
                        val leavesHost: Boolean, val status: String,
                        val summary: String?, val error: String?)
data class ResidentRun(val id: String, val ranAt: String, val status: String,
                       val note: String?)
data class ResidentTask(val id: String, val goal: String, val status: String,
                        val plannedBy: String, val nextRunAt: String?,
                        val steps: List<ResidentStep>)
data class ResidentDataset(val dataset: String, val rows: Int)
data class ResidentMatch(val key: String, val score: Double)

data class KeyVersion(val generation: Int, val active: Boolean, val createdAt: String?)
data class KeysInfo(val provider: String, val versions: List<KeyVersion>)
data class ImproveItem(val category: String, val message: String, val status: String)
data class ImproveState(val mine: List<ImproveItem>, val tally: Map<String, Int>, val total: Int)
data class AccessReportRow(val doing: String, val wall: String, val help: String?,
                           val lang: String, val createdAt: String)

class ApiException(message: String) : Exception(message)

/**
 * Coroutine client for the PDI vault backend. Every call carries the tenant
 * bearer token (`pdi_...`), issued out of band and pasted at sign-in.
 *
 * The Android emulator reaches the host machine at 10.0.2.2, so that is the
 * default. On a physical device, set your machine's LAN IP via [base].
 */
object ApiClient {
    // The trimming lives in the property's own setter rather than a
    // setBase() helper: Kotlin already generates setBase(String) for a public
    // `var`, so an explicit function by that name is a JVM signature clash.
    // qrme and jim-mini both declare the bare `var`, and this keeps the shape
    // the same while holding on to the trailing-slash and blank guards.
    @Volatile
    var base: String = "http://10.0.2.2:8000"
        set(value) {
            val trimmed = value.trimEnd('/')
            if (trimmed.isNotBlank()) field = trimmed
        }

    /**
     * The customer-managed key, for a tenant that holds its own.
     *
     * `_tenant` on the backend reads `x-tenant-key`, and a vault under
     * customer custody answers **428** to every record read and every write
     * without it. No shell sent it, so a tenant that pressed *hold our own
     * key* in the console had locked all three phones out of the vault.
     *
     * In memory, never in `SharedPreferences`: the whole promise of this
     * custody mode is that the key exists only where the customer puts it.
     * Being asked again after a relaunch is that promise working.
     */
    @Volatile
    var tenantKey: String? = null
        set(value) {
            val trimmed = value?.trim()
            field = if (trimmed.isNullOrEmpty()) null else trimmed
        }



    /** What the deployment can and cannot reach. Read-only: the posture is
     *  set in the deployment's environment, not by somebody signed in. */
    suspend fun offlineStatus(): OfflinePosture = withContext(Dispatchers.IO) {
        val o = org.json.JSONObject(request("/offline/status", "GET", null, null))
        val gs = o.optJSONArray("guarantees")
        OfflinePosture(
            o.optBoolean("offline"),
            o.optBoolean("external_transmission_possible"),
            o.optString("local_destinations_allowed"),
            (0 until (gs?.length() ?: 0)).map { gs!!.getString(it) })
    }


    data class ProblemRow(val op: String, val statusCode: Int, val count: Int,
                          val source: String, val appVersion: String,
                          val platform: String, val day: String)

    // The failure aggregate this backend keeps. Reading is the operator's:
    // the problems key as the token, or nothing when asking from the machine
    // the backend runs on.
    suspend fun problemRows(key: String): List<ProblemRow> {
        val o = JSONObject(request("/v1/problems",
            token = key.ifBlank { null }))
        val arr = o.optJSONArray("rows") ?: return emptyList()
        return (0 until arr.length()).map { i ->
            val r = arr.getJSONObject(i)
            ProblemRow(r.optString("op"), r.optInt("status_code"),
                r.optInt("count"), r.optString("source"),
                r.optString("app_version"), r.optString("platform"),
                r.optString("day"))
        }
    }

    private suspend fun request(
        path: String, method: String = "GET",
        body: JSONObject? = null, token: String? = null,
    ): String = withContext(Dispatchers.IO) {
        val conn = (URL(base + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            setRequestProperty("content-type", "application/json")
            // The language the reader actually speaks. Every sentence the
            // backend composes on a public route is chosen from this
            // header, and no native shell was sending it.
            setRequestProperty("accept-language", L10n.deviceLanguage())
            // A public route carries no bearer. Sending `Bearer null`
            // is worse than sending nothing: it is a credential the
            // server has to reject rather than an absent one.
            token?.takeIf { it.isNotBlank() }
                ?.let { setRequestProperty("authorization", "Bearer $it") }
            tenantKey?.let { setRequestProperty("x-tenant-key", it) }
            connectTimeout = 8000; readTimeout = 8000
            if (body != null) {
                doOutput = true
                outputStream.use { it.write(body.toString().toByteArray()) }
            }
        }
        val code = try {
            conn.responseCode
        } catch (e: Exception) {
            // Never reached a server. Recorded as status 0; the thrown error
            // still carries its message to the person, who owns it.
            Problems.record(method, path, 0)
            throw e
        }
        val text = (if (code in 200..299) conn.inputStream else conn.errorStream)
            ?.bufferedReader()?.use { it.readText() } ?: ""
        conn.disconnect()
        if (code !in 200..299) {
            // The status and the operation, never the detail below: these
            // messages quote what the person typed, which is theirs to read
            // and nobody's to keep.
            Problems.record(method, path, code)
            // `optString` coerces a JSONArray through toString(), so a 422 —
            // whose `detail` is pydantic's list of rows — reached the person
            // as raw JSON. `message` is the sentence the backend composes
            // beside the rows; a string `detail` still wins for everything else.
            val said = runCatching {
                val body = JSONObject(text)
                body.optString("message").ifBlank {
                    if (body.opt("detail") is String) body.optString("detail") else ""
                }
            }.getOrNull()
            throw ApiException(if (said.isNullOrBlank()) "HTTP $code" else said)
        }
        text
    }

    /** List record keys — also the sign-in validation call. */

    /**
     * Everything this deployment holds about the tenant, by table.
     *
     * Distinct from the disaster-recovery snapshot, which is ciphertext and
     * exists to be restored. This is the portability answer, and the phone
     * needs it because a person whose only device is a phone is exactly the
     * person who cannot use a desktop console to get their data out.
     */
    suspend fun exportEverything(token: String): Pair<Int, Int> =
        withContext(Dispatchers.IO) {
            val o = org.json.JSONObject(
                request("/export", "GET", null, token))
            val tables = o.optJSONObject("tables") ?: org.json.JSONObject()
            var rows = 0
            val names = tables.keys()
            while (names.hasNext()) {
                rows += tables.optJSONArray(names.next())?.length() ?: 0
            }
            Pair(tables.length(), rows)
        }

    suspend fun keys(token: String): List<String> {
        val arr = JSONObject(request("/records", token = token)).getJSONArray("keys")
        return (0 until arr.length()).map { arr.getString(it) }
    }

    suspend fun record(token: String, key: String): VaultRecord {
        val o = JSONObject(request("/records/$key", token = token))
        return VaultRecord(o.getString("key"), o.optString("value", ""), o.optString("updated_at", null))
    }

    suspend fun putRecord(token: String, key: String, value: String) {
        request("/records", "PUT", JSONObject().put("key", key).put("value", value), token)
    }

    suspend fun deleteRecord(token: String, key: String) {
        request("/records/$key", "DELETE", token = token)
    }

    suspend fun provenance(token: String, key: String): RecordProvenance {
        val o = JSONObject(request("/provenance/$key", token = token))
        val sealed = o.getJSONObject("sealed")
        return RecordProvenance(
            o.optString("origin", ""), sealed.optString("cipher", ""),
            sealed.optString("bound_to", ""), sealed.optString("created_at", ""),
            sealed.optInt("ciphertext_bytes"),
            o.getJSONObject("audit").optInt("count"),
            o.getJSONObject("chain").optBoolean("intact"))
    }

    suspend fun languages(token: String): List<LanguageInfo> {
        val arr = JSONObject(request("/languages", token = token)).getJSONArray("languages")
        return (0 until arr.length()).map { i ->
            val o = arr.getJSONObject(i)
            LanguageInfo(o.getString("code"), o.getString("label"),
                o.optBoolean("notes_translated"))
        }
    }

    suspend fun language(token: String): Pair<String, String> {
        val o = JSONObject(request("/language", token = token))
        return o.getString("language") to o.optString("mode", "pre")
    }

    suspend fun setLanguage(token: String, code: String, mode: String = "pre") {
        request("/language", "PUT",
            JSONObject().put("language", code).put("mode", mode), token)
    }

    suspend fun submitImprovement(token: String, category: String,
                                  message: String, rating: Int?) {
        val body = JSONObject().put("category", category).put("message", message)
        if (rating != null) body.put("rating", rating)
        request("/improve", "POST", body, token)
    }

    /** The accessibility door: tokenless on purpose — reporting that the
     *  vault shut you out must not require the tenant token it may have
     *  shut you out of. The words stay on the deployment. */
    suspend fun sendAccessReport(doing: String, wall: String, help: String?,
                                 lang: String): String {
        val body = JSONObject().put("doing", doing).put("wall", wall)
            .put("lang", lang)
        help?.takeIf { it.isNotBlank() }?.let { body.put("help", it) }
        return JSONObject(request("/access/reports", "POST", body))
            .optString("status", "received")
    }

    /** Admin-token read — the deployment's operator, never a tenant. */
    suspend fun accessReports(adminToken: String): List<AccessReportRow> {
        val o = JSONObject(request("/access/reports", token = adminToken))
        val arr = o.optJSONArray("reports")
        return (0 until (arr?.length() ?: 0)).map { i ->
            val r = arr!!.getJSONObject(i)
            AccessReportRow(r.optString("doing", ""), r.optString("wall", ""),
                r.optString("help", "").takeIf { it.isNotBlank() },
                r.optString("lang", ""), r.optString("created_at", ""))
        }
    }

    suspend fun improvements(token: String): ImproveState {
        val o = JSONObject(request("/improve", token = token))
        val mineArr = o.optJSONArray("mine")
        val mine = (0 until (mineArr?.length() ?: 0)).map { i ->
            val m = mineArr!!.getJSONObject(i)
            ImproveItem(m.optString("category", ""), m.optString("message", ""),
                m.optString("status", ""))
        }
        val tallyObj = o.optJSONObject("tally") ?: JSONObject()
        val tally = tallyObj.keys().asSequence().associateWith { tallyObj.optInt(it) }
        return ImproveState(mine, tally, o.optInt("total"))
    }

    // ---- admin: key management (PDI_ADMIN_TOKEN, never the tenant token) ----

    private fun parseKeys(o: JSONObject): KeysInfo {
        val arr = o.optJSONArray("versions")
        return KeysInfo(o.optString("provider", "env"),
            (0 until (arr?.length() ?: 0)).map { i ->
                val v = arr!!.getJSONObject(i)
                KeyVersion(v.optInt("generation"), v.optBoolean("active"),
                    v.optString("created_at", null))
            })
    }

    suspend fun adminKeys(adminToken: String): KeysInfo =
        parseKeys(JSONObject(request("/keys", token = adminToken)))

    suspend fun rotateKey(adminToken: String): KeysInfo {
        // Server default reseals every record immediately.
        request("/keys/rotate", "POST", JSONObject(), adminToken)
        return adminKeys(adminToken)
    }

    suspend fun retireKeys(adminToken: String): Pair<Int, KeysInfo> {
        val o = JSONObject(request("/keys/retire", "POST", JSONObject(), adminToken))
        return o.optInt("retired") to parseKeys(o)
    }

    /**
     * Section 10's five acceptance criteria, run against this deployment.
     *
     * The rows come back whole rather than as a count. A shell that reported
     * "3 of 5" and could not name which two failed would be the binding that
     * decoded the answer and returned a tally of what it discarded.
     */
    suspend fun acceptance(token: String): AcceptanceReport {
        val o = JSONObject(request("/acceptance", token = token))
        val arr = o.optJSONArray("checks") ?: JSONArray()
        return AcceptanceReport(
            o.optString("at", ""), o.optInt("passing"), o.optInt("of"),
            o.optBoolean("clean"),
            (0 until arr.length()).map { i ->
                val c = arr.getJSONObject(i)
                AcceptanceCheck(c.optString("check", ""), c.optString("says", ""),
                    c.optBoolean("passed"), c.optString("detail", ""))
            })
    }

    suspend fun auditVerify(token: String): Boolean {
        return JSONObject(request("/audit/verify", token = token)).optBoolean("intact")
    }

    suspend fun auditEntries(token: String): List<AuditEntry> {
        val arr = JSONArray(request("/audit", token = token))
        return (0 until arr.length()).map { i ->
            val o = arr.getJSONObject(i)
            AuditEntry(o.optInt("seq"), o.optString("action", ""),
                o.optString("ref", null), o.optString("at", ""), o.optString("category", null))
        }
    }

    // ---- robots as vault-backed data sources ----

    private fun robotOf(o: JSONObject) = Robot(
        o.getString("id"), o.optString("model", ""), o.optString("name", ""),
        o.optString("status", null), o.optInt("collected"))

    suspend fun roboticsCatalog(token: String): List<RobotSpec> {
        val arr = JSONObject(request("/robotics/catalog", token = token))
            .getJSONArray("robots")
        return (0 until arr.length()).map { i ->
            val o = arr.getJSONObject(i)
            RobotSpec(o.getString("model"), o.getString("label"), o.getString("maker"))
        }
    }

    suspend fun robots(token: String): List<Robot> {
        val arr = JSONArray(request("/robots", token = token))
        return (0 until arr.length()).map { robotOf(arr.getJSONObject(it)) }
    }

    suspend fun bindRobot(token: String, model: String): Robot {
        return robotOf(JSONObject(request("/robots", "POST",
            JSONObject().put("model", model), token)))
    }

    suspend fun ingest(token: String, rid: String, kind: String, content: String): IngestResult {
        val o = JSONObject(request("/robots/$rid/ingest", "POST",
            JSONObject().put("kind", kind).put("content", content), token))
        return IngestResult(o.optBoolean("sealed_at_rest"), o.getString("key"))
    }

    suspend fun robotKeys(token: String, rid: String): List<String> {
        val arr = JSONObject(request("/robots/$rid/data", token = token))
            .getJSONArray("keys")
        return (0 until arr.length()).map { arr.getString(it) }
    }

    // ---- compliance-grade secure transfers ----

    private fun transferOf(o: JSONObject): Transfer {
        val progs = o.optJSONArray("program_keys")
        return Transfer(o.getString("id"), o.optString("recipient", ""),
            o.optString("filename", ""), o.optString("status", ""),
            (0 until (progs?.length() ?: 0)).map { progs!!.getString(it) },
            o.optString("expires_at", null), o.optString("receive_token", null))
    }

    suspend fun compliancePrograms(token: String): List<ComplianceProgram> {
        val arr = JSONObject(request("/compliance/programs", token = token))
            .getJSONArray("programs")
        return (0 until arr.length()).map { i ->
            val o = arr.getJSONObject(i)
            ComplianceProgram(o.getString("key"), o.getString("label"))
        }
    }

    // ---- the key itself: whose hands it is in ----

    suspend fun tenantKey(token: String): String =
        JSONObject(request("/key", token = token)).optString("note")

    suspend fun setTenantKey(token: String, provider: String,
                             key: String?): String {
        val body = JSONObject().put("provider", provider)
        if (!key.isNullOrBlank()) body.put("key", key)
        return JSONObject(request("/key", "PUT", body, token))
            .optString("note")
    }

    /** Hands the tenant back to deployment custody. A 409 if it never
     *  left, which the operator needs told rather than shown as a
     *  failure. */
    suspend fun surrenderTenantKey(token: String): String =
        JSONObject(request("/key", "DELETE", token = token))
            .optString("note")

    suspend fun resealUnderNewKey(adminToken: String): String {
        val o = JSONObject(request("/keys/reseal", "POST", token = adminToken))
        return "v${o.optInt("active_version")} \u00b7 " +
            "${o.optInt("resealed")} \u00b7 " +
            "${o.optInt("customer_managed_skipped")}"
    }

    suspend fun revokeToken(adminToken: String, minted: String): String =
        request("/tokens/$minted", "DELETE", token = adminToken)

    // ---- connectors: the catalog, and each connection's own code ----

    suspend fun connectorCatalog(): Int {
        val o = JSONObject(request("/connectors/catalog"))
        o.keys().forEach { k ->
            o.optJSONArray(k)?.let { return it.length() }
            o.optJSONObject(k)?.let { return it.length() }
        }
        return o.length()
    }

    suspend fun connectorBeacon(token: String, cid: String): String =
        request("/connectors/$cid/beacon", token = token)

    fun connectorQrUrl(cid: String): String =
        java.net.URL("$base/connectors/$cid/qr.svg").toString()

    suspend fun unbindRobot(token: String, rid: String): String =
        request("/robots/$rid", "DELETE", token = token)

    // ---- the guide, the pane in the corner, and the translator ----

    suspend fun guideOutline(): Int =
        JSONObject(request("/console/guide")).optInt("steps")

    data class GuideStepK(val key: String, val title: String, val said: String)

    private fun stepOf(o: JSONObject): GuideStepK = GuideStepK(
        o.optString("key"), o.optString("title"),
        o.optString("what", o.optString("speak")))

    suspend fun guideStep(key: String): GuideStepK =
        stepOf(JSONObject(request("/console/guide/steps/$key")))

    suspend fun guideForScreen(number: Int): GuideStepK =
        stepOf(JSONObject(request("/console/guide/for-screen/$number")))

    data class GuideWhereK(val step: GuideStepK?, val done: Int,
                           val total: Int, val note: String)

    private fun whereOf(o: JSONObject): GuideWhereK = GuideWhereK(
        o.optJSONObject("step")?.let { stepOf(it) },
        o.optInt("done"), o.optInt("total"), o.optString("note"))

    suspend fun guideStart(learner: String): GuideWhereK =
        whereOf(JSONObject(request("/console/guide/start", "POST",
            JSONObject().put("learner_id", learner))))

    suspend fun guideProgress(learner: String): GuideWhereK =
        whereOf(JSONObject(request("/console/guide/progress/$learner")))

    suspend fun guideDone(learner: String, lesson: String): GuideWhereK =
        whereOf(JSONObject(request("/console/guide/done", "POST",
            JSONObject().put("learner_id", learner).put("lesson", lesson))))

    suspend fun consoleAsk(question: String): String =
        JSONObject(request("/console/ask", "POST",
            JSONObject().put("question", question))).optString("answer")

    /** Dictionary-only on the backend: PDI runs no model, so it translates
     *  exactly its own note strings and the engine field says which
     *  happened. */
    suspend fun translate(token: String, text: String): String {
        val o = JSONObject(request("/translate", "POST",
            JSONObject().put("text", text), token))
        return o.optString("translation") + " \u00b7 " + o.optString("engine")
    }

    suspend fun dockVocabulary(): String {
        val o = JSONObject(request("/dock/faces"))
        return o.optString("default_face") + " \u00b7 " +
            o.optString("default_state")
    }

    suspend fun dockWhere(face: String): String {
        val o = JSONObject(request("/dock/where/$face"))
        return o.optString("title") + " \u00b7 " + o.optString("path")
    }

    data class DockSettingsK(val corner: String, val state: String,
                             val face: String)

    private fun dockOf(o: JSONObject): DockSettingsK = DockSettingsK(
        o.optString("corner"), o.optString("state"), o.optString("face"))

    suspend fun dockSettings(token: String, tid: String): DockSettingsK =
        dockOf(JSONObject(request("/dock/$tid", token = token)))

    suspend fun dockConfigure(token: String, tid: String,
                              corner: String): DockSettingsK =
        dockOf(JSONObject(request("/dock/$tid", "PUT",
            JSONObject().put("corner", corner), token)))

    suspend fun dockFace(token: String, tid: String, name: String): String =
        JSONObject(request("/dock/$tid/face/$name", token = token))
            .optString("shows")

    // ---- exchange details: one transfer, one intake, their chains ----

    suspend fun transferOne(token: String, tid: String): String =
        request("/transfers/$tid", token = token)

    suspend fun transferCustody(token: String, tid: String): CustodyChainK =
        chainOf(JSONObject(request("/transfers/$tid/custody", token = token)))

    /** The recipient's act — the one-shot receive token is the whole
     *  credential, riding as its own header the way the submit does. */
    suspend fun receiveTransfer(tid: String, receiveToken: String): String =
        withContext(Dispatchers.IO) {
        val conn = (URL("$base/transfers/$tid/receive").openConnection()
            as HttpURLConnection).apply {
            requestMethod = "POST"
            setRequestProperty("accept-language", L10n.deviceLanguage())
            setRequestProperty("x-receive-token", receiveToken)
        }
        JSONObject(conn.inputStream.bufferedReader().readText())
            .optString("filename", "file")
    }

    suspend fun intakeOne(token: String, iid: String): String =
        request("/intakes/$iid", token = token)

    suspend fun intakeCustody(token: String, iid: String): CustodyChainK =
        chainOf(JSONObject(request("/intakes/$iid/custody", token = token)))

    private fun chainOf(o: JSONObject): CustodyChainK {
        val events = mutableListOf<String>()
        o.optJSONArray("chain_of_custody")?.let { a ->
            for (i in 0 until a.length()) {
                val e = a.getJSONObject(i)
                events.add("${e.optString("event")} — ${e.optString("actor")}")
            }
        }
        return CustodyChainK(o.optBoolean("audit_chain_intact"), events)
    }

    // ---- positions: the assistant builder ----

    suspend fun buildPosition(token: String, industry: String,
                              jobTitle: String): String {
        val o = JSONObject(request("/positions", "POST",
            JSONObject().put("industry", industry)
                .put("role", JSONObject().put("job_title", jobTitle)), token))
        return "${o.optString("id")} \u00b7 ${o.optString("industry")}"
    }

    suspend fun listPositions(token: String): Pair<Int, String?> {
        val o = JSONObject(request("/positions", token = token))
        val first = o.optJSONArray("ids")?.optString(0)
        return Pair(o.optInt("count"), first?.ifEmpty { null })
    }

    suspend fun getPosition(token: String, id: String): String {
        val o = JSONObject(request("/positions/$id", token = token))
        return "${o.optString("id")} \u00b7 ${o.optString("industry")}"
    }

    // ---- posture: where the vault lives, and whether it is up ----

    /**
     * The backend's own version, for the guard that compares it with this
     * build's. Empty when the field is absent, which is a real answer and
     * not an error: a backend old enough to predate the field is exactly
     * the deployment the guard exists to name. `health` above reads the
     * same response and throws this away, which is why nothing on this
     * shell could tell a stale backend from a current one.
     */
    suspend fun backendVersion(): String {
        return JSONObject(request("/health")).optString("version", "")
    }

    suspend fun health(): String =
        JSONObject(request("/health")).optString("status")

    suspend fun hostingModes(): List<HostingModeK> {
        val o = JSONObject(request("/hosting")).optJSONObject("modes")
            ?: return emptyList()
        return o.keys().asSequence().map { id ->
            val m = o.getJSONObject(id)
            HostingModeK(id, m.optString("title"), m.optString("price"),
                m.optString("means"), m.optString("free_because"),
                joined(m, "we_are_responsible_for"),
                joined(m, "you_are_responsible_for"))
        }.toList()
    }

    suspend fun hosting(token: String, tid: String): HostingModeK {
        val m = JSONObject(request("/hosting/$tid", token = token))
        return HostingModeK(m.optString("mode"), m.optString("title"),
            m.optString("price"), m.optString("means"),
            m.optString("free_because"),
            joined(m, "we_are_responsible_for"),
            joined(m, "you_are_responsible_for"))
    }

    suspend fun hostingHistory(token: String, tid: String): Int =
        JSONObject(request("/hosting/$tid/history", token = token))
            .optJSONArray("history")?.length() ?: 0

    suspend fun setHosting(token: String, tid: String, mode: String): String =
        request("/hosting/$tid", "PUT", JSONObject().put("mode", mode), token)

    suspend fun recordDeployment(token: String): String =
        request("/deployments", "POST", JSONObject().put("name", "new site")
            .put("option", "colocation"), token)

    suspend fun operations(token: String): Int =
        JSONObject(request("/operations", token = token))
            .optJSONArray("entries")?.length() ?: 0

    suspend fun auditSchema(): String {
        val o = JSONObject(request("/audit/schema"))
        return "${o.optJSONArray("actions")?.length() ?: 0} \u00b7 " +
            o.optString("retention")
    }

    /** The tenant's own standing — executed, since when, and the refusal
     *  note when nothing is on file. Names live on the admin route only. */
    suspend fun baaStatus(token: String): String {
        val o = JSONObject(request("/baa", token = token))
        return if (o.optBoolean("executed"))
            o.optString("effective_date", "\u2713")
        else o.optString("note")
    }

    private fun joined(o: JSONObject, name: String): String {
        val a = o.optJSONArray(name) ?: return ""
        return (0 until a.length()).joinToString(", ") { a.getString(it) }
    }

    // ---- continuity: bequests, and what outlives the tenant ----

    suspend fun bequests(token: String): List<BequestK> {
        val arr = JSONArray(request("/bequests", token = token))
        return (0 until arr.length()).map { bequestOf(arr.getJSONObject(it)) }
    }

    suspend fun createBequest(token: String, grantee: String,
                              prefixes: List<String>, note: String?): BequestK {
        val pfx = JSONArray(); prefixes.forEach { pfx.put(it) }
        val body = JSONObject().put("grantee_name", grantee)
            .put("key_prefixes", pfx)
        if (!note.isNullOrBlank()) body.put("note", note)
        return bequestOf(JSONObject(request("/bequests", "POST", body, token)))
    }

    suspend fun revokeBequest(token: String, bid: String): BequestK =
        bequestOf(JSONObject(request("/bequests/$bid", "DELETE", token = token)))

    /** The executor's act: activation attests the condition — the reference
     *  goes into the audit chain — and mints the grant token, shown once. */
    suspend fun activateBequest(adminToken: String, bid: String,
                                ref: String): BequestK =
        bequestOf(JSONObject(request("/bequests/$bid/activate", "POST",
            JSONObject().put("activation_ref", ref), adminToken)))

    suspend fun revokeBequestGrant(adminToken: String, bid: String): Boolean =
        JSONObject(request("/bequests/$bid/grant", "DELETE",
            token = adminToken)).optBoolean("revoked")

    /** The heir's side. Two separate secrets on purpose — the grant token
     *  says the condition was attested, the customer key decrypts — so both
     *  ride as headers on a connection opened here, in the shape the route
     *  audit reads. */
    suspend fun bequestKeys(grantToken: String, customerKey: String):
        List<String> = withContext(Dispatchers.IO) {
        val conn = (URL("$base/bequests/grant/keys").openConnection()
            as HttpURLConnection).apply {
            requestMethod = "GET"
            setRequestProperty("accept-language", L10n.deviceLanguage())
            setRequestProperty("x-grant-token", grantToken)
            setRequestProperty("x-tenant-key", customerKey)
        }
        val o = JSONObject(conn.inputStream.bufferedReader().readText())
        val out = mutableListOf<String>()
        o.optJSONArray("keys")?.let { a ->
            for (i in 0 until a.length()) out.add(a.getString(i))
        }
        out
    }

    suspend fun bequestRead(key: String, grantToken: String,
                            customerKey: String): String =
        withContext(Dispatchers.IO) {
        val conn = (URL("$base/bequests/grant/read?key=$key").openConnection()
            as HttpURLConnection).apply {
            requestMethod = "GET"
            setRequestProperty("accept-language", L10n.deviceLanguage())
            setRequestProperty("x-grant-token", grantToken)
            setRequestProperty("x-tenant-key", customerKey)
        }
        conn.inputStream.bufferedReader().readText()
    }

    private fun bequestOf(o: JSONObject): BequestK {
        val pfx = mutableListOf<String>()
        o.optJSONArray("key_prefixes")?.let { a ->
            for (i in 0 until a.length()) pfx.add(a.getString(i))
        }
        return BequestK(o.optString("id"), o.optString("grantee_name"),
            o.optString("condition"), pfx, o.optBoolean("activated"),
            o.optBoolean("revoked"), o.optString("grant_token", ""))
    }

    // ---- contributions, the snapshot, and the custody ops ----

    suspend fun contributions(token: String): Int =
        JSONObject(request("/contributions", token = token)).optInt("count")

    suspend fun contribute(token: String, source: String, ref: String?): String {
        val body = JSONObject().put("source", source).put("kind", "outcome")
            .put("payload", JSONObject().put("helped", true))
        if (!ref.isNullOrBlank()) body.put("ref", ref)
        return JSONObject(request("/contributions", "POST", body, token))
            .optString("key")
    }

    suspend fun withdrawContribution(token: String, ref: String): String =
        request("/contributions/$ref", "DELETE", token = token)

    /** The whole tenant, in hand — raw on purpose: records are arbitrary
     *  JSON and the door is the fetch, not a schema. Held so a restore can
     *  put back exactly what was taken. */
    private var lastSnapshot: JSONArray? = null

    suspend fun snapshotRecords(token: String): Int {
        val o = JSONObject(request("/snapshot", token = token))
        lastSnapshot = o.optJSONArray("records")
        return lastSnapshot?.length() ?: 0
    }

    suspend fun restoreSnapshot(token: String): String =
        request("/restore", "POST",
            JSONObject().put("records", lastSnapshot ?: JSONArray()), token)

    suspend fun retentionPolicy(adminToken: String): String =
        JSONObject(request("/retention", token = adminToken))
            .optString("recovery_window")

    suspend fun retentionSweep(adminToken: String): String {
        val o = JSONObject(request("/retention/sweep", "POST",
            token = adminToken))
        return "${o.optInt("purged_tenants")} \u00b7 " +
            "${o.optInt("expired_records")} \u00b7 " +
            o.optString("recovery_window")
    }

    suspend fun seedDemo(adminToken: String): String =
        request("/seed", "POST", token = adminToken)

    // ---- tenants: the operator's half ----

    suspend fun createTenant(adminToken: String, name: String): TenantMadeK {
        val o = JSONObject(request("/tenants", "POST",
            JSONObject().put("name", name), adminToken))
        return TenantMadeK(o.optString("id"), o.optString("name"),
            o.optString("token"))
    }

    suspend fun restoreTenant(adminToken: String, tid: String): String =
        request("/tenants/$tid/restore", "POST", token = adminToken)

    /** `mode` decides whether the tenant can come back. The audit trail
     *  survives either way — that is the point of a hash chain. */
    suspend fun deleteTenant(adminToken: String, tid: String,
                             mode: String): String =
        request("/tenants/$tid?mode=$mode", "DELETE", token = adminToken)

    suspend fun mintTenantToken(adminToken: String, tid: String,
                                role: String): String =
        JSONObject(request("/tenants/$tid/tokens", "POST",
            JSONObject().put("role", role), adminToken)).optString("token")

    suspend fun setTenantRetention(adminToken: String, tid: String,
                                   retention: String): String =
        JSONObject(request("/tenants/$tid/retention", "PUT",
            JSONObject().put("retention", retention), adminToken))
            .optString("retention")

    suspend fun tenantBaa(adminToken: String, tid: String): BaaK =
        baaOf(JSONObject(request("/tenants/$tid/baa", token = adminToken)))

    suspend fun recordTenantBaa(adminToken: String, tid: String,
                                customer: String, operatorName: String,
                                date: String): BaaK =
        baaOf(JSONObject(request("/tenants/$tid/baa", "POST",
            JSONObject().put("customer_legal_name", customer)
                .put("operator_legal_name", operatorName)
                .put("effective_date", date), adminToken)))

    suspend fun rescindTenantBaa(adminToken: String, tid: String): String =
        request("/tenants/$tid/baa", "DELETE", token = adminToken)

    private fun baaOf(o: JSONObject) = BaaK(o.optBoolean("executed"),
        o.optString("customer_legal_name"), o.optString("operator_legal_name"),
        o.optString("effective_date"))

    // ---- the agent at the gate ----

    suspend fun gateCeiling(token: String): GateCeilingK {
        val o = JSONObject(request("/gate/ceiling", token = token))
        fun keys(name: String): List<String> {
            val obj = o.optJSONObject(name) ?: return emptyList()
            return obj.keys().asSequence().toList().sorted()
        }
        return GateCeilingK(o.optString("rule"), keys("may"), keys("may_never"))
    }

    suspend fun gateChannel(token: String): GateChannelK {
        val o = JSONObject(request("/gate/channel", token = token))
        return GateChannelK(o.optBoolean("configured"), o.optBoolean("signed"))
    }

    suspend fun gateRoster(token: String): GateRosterK {
        val o = JSONObject(request("/gate/roster", token = token))
        val entries = mutableListOf<RosterEntryK>()
        o.optJSONArray("roster")?.let { a ->
            for (i in 0 until a.length()) {
                val e = a.getJSONObject(i)
                entries.add(RosterEntryK(e.optString("id"),
                    e.optString("name"), e.optString("role")))
            }
        }
        return GateRosterK(o.optBoolean("configured"), entries,
            o.optBoolean("anybody_on_shift"))
    }

    suspend fun addToRoster(token: String, name: String, role: String): String =
        request("/gate/roster", "POST",
            JSONObject().put("name", name).put("role", role), token)

    suspend fun removeFromRoster(token: String, rid: String): Boolean =
        JSONObject(request("/gate/roster/$rid", "DELETE", token = token))
            .optBoolean("removed")

    suspend fun setGateTimezone(token: String, timezone: String): String =
        JSONObject(request("/gate/timezone", "PUT",
            JSONObject().put("timezone", timezone), token))
            .optString("timezone")

    suspend fun gatePages(token: String): List<GatePageK> {
        val arr = JSONArray(request("/gate/pages", token = token))
        return (0 until arr.length()).map {
            val o = arr.getJSONObject(it)
            GatePageK(o.optString("id"), o.optString("state"))
        }
    }

    suspend fun retryGatePage(token: String, pid: String): String =
        request("/gate/pages/$pid/retry", "POST", token = token)

    // ---- carriers: custody codes on sealed things ----

    suspend fun carrierBeacons(token: String): List<CarrierBeacon> {
        val arr = JSONArray(request("/beacons", token = token))
        return (0 until arr.length()).map { beaconOf(arr.getJSONObject(it)) }
    }

    suspend fun placeCarrierBeacon(token: String, label: String,
                                   disclose: String): CarrierBeacon =
        beaconOf(JSONObject(request("/beacons", "POST",
            JSONObject().put("ref_kind", "object").put("label", label)
                .put("disclose", disclose), token)))

    suspend fun carrierBeacon(token: String, bid: String): CarrierBeacon =
        beaconOf(JSONObject(request("/beacons/$bid", token = token)))

    suspend fun setCarrierState(token: String, bid: String,
                                state: String): CarrierBeacon =
        beaconOf(JSONObject(request("/beacons/$bid/state", "PUT",
            JSONObject().put("state", state), token)))

    suspend fun liftCarrierBeacon(token: String, bid: String): Boolean =
        JSONObject(request("/beacons/$bid", "DELETE", token = token))
            .optBoolean("active")

    suspend fun carrierCustody(token: String, bid: String): CustodyChainK {
        val o = JSONObject(request("/beacons/$bid/custody", token = token))
        val events = mutableListOf<String>()
        o.optJSONArray("chain_of_custody")?.let { a ->
            for (i in 0 until a.length()) {
                val e = a.getJSONObject(i)
                events.add("${e.optString("event")} — ${e.optString("actor")}"
                    + " · ${e.optString("at")}")
            }
        }
        return CustodyChainK(o.optBoolean("audit_chain_intact"), events)
    }

    /** The scanner's half — no bearer at all: the code in the hand is the
     *  whole credential, and what it earns is capped by `disclose`. */
    suspend fun scanCard(bid: String): ScanCardK {
        val o = JSONObject(request("/s/$bid/card"))
        return ScanCardK(o.optString("reference"), o.optString("kind"),
            o.optString("state"), o.optBoolean("under_custody"),
            o.optString("badge"), o.optString("note"))
    }

    /** The landing page and its QR image: the JSON helper cannot carry
     *  either, so the door is the URL the opener fetches, and building it
     *  here is what the route audit reads. */
    fun scanPageUrl(bid: String): String =
        java.net.URL("$base/s/$bid").toString()

    fun scanQrUrl(bid: String): String =
        java.net.URL("$base/s/$bid/qr.svg").toString()

    suspend fun reportFound(bid: String): String =
        JSONObject(request("/s/$bid/found", "POST",
            JSONObject().put("where", "loading dock"))).optString("note")

    suspend fun ringHolder(bid: String): RingK =
        ringOf(JSONObject(request("/s/$bid/ring", "POST",
            JSONObject().put("kind", "delivery"))))

    suspend fun rings(token: String): List<RingK> {
        val arr = JSONArray(request("/rings", token = token))
        return (0 until arr.length()).map { ringOf(arr.getJSONObject(it)) }
    }

    suspend fun ringTranscript(token: String, rid: String): RingK =
        ringOf(JSONObject(request("/rings/$rid/transcript", token = token)))

    /** Resolve the recipient's page before the link goes into an email — a
     *  misconfigured public base is otherwise discovered by the recipient,
     *  who has nobody to ask. */
    suspend fun checkRecipientPage(tid: String): Boolean =
        request("/r/$tid").isNotEmpty()

    /** How to open this console on a phone: same Wi-Fi, no app store. */
    suspend fun pairInfo(): PairInfoK {
        val o = JSONObject(request("/pair"))
        val how = mutableListOf<String>()
        o.optJSONArray("how")?.let { a ->
            for (i in 0 until a.length()) how.add(a.getString(i))
        }
        return PairInfoK(o.optString("console_url"), how, o.optString("note"))
    }

    fun pairQrUrl(): String = java.net.URL("$base/pair/qr.svg").toString()

    private fun beaconOf(o: JSONObject) = CarrierBeacon(
        o.optString("id"), o.optString("ref_kind"), o.optString("label"),
        o.optString("disclose"), o.optString("state"), o.optInt("scans"),
        o.optBoolean("active"))

    private fun ringOf(o: JSONObject) = RingK(o.optString("id"),
        o.optString("kind"), o.optString("note"), o.optString("state"),
        o.optString("outcome"), o.optString("created_at"))

    suspend fun transfers(token: String): List<Transfer> {
        val arr = JSONArray(request("/transfers", token = token))
        return (0 until arr.length()).map { transferOf(arr.getJSONObject(it)) }
    }

    suspend fun createTransfer(token: String, recipient: String, filename: String,
                               content: String, programs: List<String>): Transfer {
        val progs = org.json.JSONArray()
        programs.forEach { progs.put(it) }
        return transferOf(JSONObject(request("/transfers", "POST",
            JSONObject().put("recipient", recipient).put("filename", filename)
                .put("content", content).put("programs", progs), token)))
    }

    suspend fun revokeTransfer(token: String, tid: String) {
        request("/transfers/$tid", "DELETE", token = token)
    }

    // ---- secure intake ----

    private fun intakeOf(o: JSONObject): Intake {
        val progs = o.optJSONArray("program_keys")
        return Intake(o.getString("id"), o.optString("from_party", ""),
            o.optString("purpose", null), o.optString("status", ""),
            (0 until (progs?.length() ?: 0)).map { progs!!.getString(it) },
            o.optString("filename", null), o.optString("submit_token", null))
    }

    suspend fun intakes(token: String): List<Intake> {
        val arr = JSONArray(request("/intakes", token = token))
        return (0 until arr.length()).map { intakeOf(arr.getJSONObject(it)) }
    }

    suspend fun createIntake(token: String, fromParty: String, purpose: String?,
                             programs: List<String>): Intake {
        val progs = org.json.JSONArray()
        programs.forEach { progs.put(it) }
        val body = JSONObject().put("from_party", fromParty).put("programs", progs)
        if (!purpose.isNullOrBlank()) body.put("purpose", purpose)
        return intakeOf(JSONObject(request("/intakes", "POST", body, token)))
    }

    suspend fun intakeFile(token: String, iid: String): IntakeFile {
        val o = JSONObject(request("/intakes/$iid/file", token = token))
        return IntakeFile(o.optString("filename", null), o.optString("content", null))
    }

    suspend fun closeIntake(token: String, iid: String) {
        request("/intakes/$iid", "DELETE", token = token)
    }

    // ---- social-platform connectors (tenant data sources) ----

    private fun connOf(o: JSONObject) = SocialConn(
        o.getString("id"), o.optString("platform", ""), o.optString("direction", ""),
        o.optString("handle", null), o.optString("status", null))

    // -- the resident intelligence (pdi/resident.py) ------------------------

    private fun residentTaskOf(o: JSONObject): ResidentTask {
        val steps = o.getJSONArray("plan_steps")
        return ResidentTask(
            id = o.getString("id"), goal = o.getString("goal"),
            status = o.getString("status"),
            plannedBy = o.getString("planned_by"),
            nextRunAt = if (o.isNull("next_run_at")) null
                        else o.optString("next_run_at"),
            steps = (0 until steps.length()).map { i ->
                val s = steps.getJSONObject(i)
                ResidentStep(
                    position = s.getInt("position"),
                    title = s.getString("title"),
                    tool = s.getString("tool"),
                    leavesHost = s.getBoolean("leaves_host"),
                    status = s.getString("status"),
                    summary = s.optString("summary").takeIf { it.isNotBlank() },
                    error = s.optString("error").takeIf { it.isNotBlank() })
            })
    }

    suspend fun residentPosture(token: String): ResidentPosture {
        val o = JSONObject(request("/resident", token = token))
        val tools = o.getJSONArray("tools")
        return ResidentPosture(
            means = o.getString("means"),
            hostingMode = o.getString("hosting_mode"),
            localModel = o.optString("local_model").takeIf { it.isNotBlank() && it != "null" },
            embedder = o.getString("embedder"),
            tools = (0 until tools.length()).map { i ->
                val tl = tools.getJSONObject(i)
                ResidentTool(tl.getString("name"), tl.getString("means"),
                             tl.getBoolean("leaves_host"))
            },
            privacy = o.getString("privacy"))
    }

    suspend fun residentPlan(token: String, goal: String,
                             everyHours: Double? = null): ResidentTask {
        val body = JSONObject().put("goal", goal)
        // A standing task: the vault re-runs the plan on this interval.
        if (everyHours != null) body.put("every_hours", everyHours)
        return residentTaskOf(JSONObject(request("/resident/tasks", "POST",
            body, token)))
    }

    // The off switch: end a task's future; the record of its runs stays.
    suspend fun residentCancel(token: String, tid: String): Boolean {
        val o = JSONObject(request("/resident/tasks/$tid", "DELETE",
                                   null, token))
        return o.optBoolean("cancelled")
    }

    suspend fun residentTasks(token: String): List<ResidentTask> {
        val arr = JSONArray(request("/resident/tasks", token = token))
        return (0 until arr.length()).map { residentTaskOf(arr.getJSONObject(it)) }
    }

    suspend fun residentRun(token: String, tid: String): ResidentTask =
        residentTaskOf(JSONObject(
            request("/resident/tasks/$tid/run", "POST", null, token)))

    suspend fun residentRuns(token: String, tid: String): List<ResidentRun> {
        val arr = JSONArray(request("/resident/tasks/$tid/runs", token = token))
        return (0 until arr.length()).map {
            val r = arr.getJSONObject(it)
            ResidentRun(r.getString("id"), r.getString("ran_at"),
                        r.getString("status"),
                        if (r.isNull("note")) null else r.optString("note"))
        }
    }

    suspend fun residentDatasets(token: String): List<ResidentDataset> {
        val arr = JSONArray(request("/resident/datasets", token = token))
        return (0 until arr.length()).map {
            val d = arr.getJSONObject(it)
            ResidentDataset(d.getString("dataset"), d.getInt("row_count"))
        }
    }

    /// Rows are whatever columns the plan wrote, so they are shown as the
    /// JSON they are rather than decoded into a shape this shell invents.
    suspend fun residentRows(token: String, name: String): List<String> {
        val o = JSONObject(request("/resident/datasets/$name/rows",
                                   token = token))
        val arr = o.getJSONArray("dataset_rows")
        return (0 until arr.length()).map { arr.getJSONObject(it).toString() }
    }

    suspend fun residentEmbed(token: String, key: String, text: String): String {
        val o = JSONObject(request("/resident/embeddings", "POST",
            JSONObject().put("key", key).put("text", text), token))
        return o.getString("embedder")
    }

    suspend fun residentForget(token: String, key: String): Int {
        val o = JSONObject(request("/resident/embeddings/$key", "DELETE",
                                   null, token))
        return o.getInt("vectors_removed")
    }

    suspend fun residentSearch(token: String, query: String): List<ResidentMatch> {
        val o = JSONObject(request("/resident/search", "POST",
            JSONObject().put("query", query), token))
        val arr = o.getJSONArray("matches")
        return (0 until arr.length()).map {
            val m = arr.getJSONObject(it)
            ResidentMatch(m.getString("key"), m.getDouble("score"))
        }
    }

    // One local turn from the vault's own model — the prompt never
    // leaves the host, and the answer names which engine spoke.
    suspend fun residentInfer(token: String, prompt: String): String {
        val o = JSONObject(request("/resident/infer", "POST",
            JSONObject().put("prompt", prompt), token))
        return o.getString("model") + " \u00b7 " + o.getString("text")
    }

    // Grounded: the question ranks this tenant's vectors, the matched
    // seals are read back, and the local model answers from them.
    suspend fun residentAsk(token: String, question: String): String {
        val o = JSONObject(request("/resident/ask", "POST",
            JSONObject().put("question", question), token))
        val keys = o.getJSONArray("drew_on")
        val drew = (0 until keys.length()).joinToString(" ") {
            keys.getString(it) }
        return o.getString("model") + " \u00b7 " + o.getString("text") +
            (if (drew.isEmpty()) "" else " \u00b7 " + drew)
    }

    suspend fun connectors(token: String): List<SocialConn> {
        val arr = JSONArray(request("/connectors", token = token))
        return (0 until arr.length()).map { connOf(arr.getJSONObject(it)) }
    }

    suspend fun createConnector(token: String, platform: String, direction: String,
                                handle: String?): SocialConn {
        val body = JSONObject().put("platform", platform).put("direction", direction)
        if (!handle.isNullOrBlank()) body.put("handle", handle)
        return connOf(JSONObject(request("/connectors", "POST", body, token)))
    }

    suspend fun connectorIngest(token: String, cid: String, content: String) {
        val items = org.json.JSONArray().put(JSONObject().put("content", content))
        request("/connectors/$cid/ingest", "POST", JSONObject().put("items", items), token)
    }

    suspend fun connectorScrape(token: String, cid: String) {
        request("/connectors/$cid/scrape", "POST", JSONObject(), token)
    }

    suspend fun connectorPublish(token: String, cid: String, content: String) {
        request("/connectors/$cid/publish", "POST",
            JSONObject().put("content", content), token)
    }

    suspend fun revokeConnector(token: String, cid: String) {
        request("/connectors/$cid", "DELETE", token = token)
    }

    /** The sender's side: authenticated by the one-shot X-Submit-Token, not
     * the tenant bearer. */
    suspend fun submitIntake(iid: String, submitToken: String, filename: String,
                             content: String): Unit = withContext(Dispatchers.IO) {
        val conn = (URL("$base/intakes/$iid/submit").openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            setRequestProperty("content-type", "application/json")
            // The language the reader actually speaks. Every sentence the
            // backend composes on a public route is chosen from this
            // header, and no native shell was sending it.
            setRequestProperty("accept-language", L10n.deviceLanguage())
            setRequestProperty("X-Submit-Token", submitToken)
            connectTimeout = 8000; readTimeout = 8000
            doOutput = true
            outputStream.use {
                it.write(JSONObject().put("filename", filename)
                    .put("content", content).toString().toByteArray())
            }
        }
        val code = conn.responseCode
        val text = (if (code in 200..299) conn.inputStream else conn.errorStream)
            ?.bufferedReader()?.use { it.readText() } ?: ""
        conn.disconnect()
        if (code !in 200..299) {
            // `optString` coerces a JSONArray through toString(), so a 422 —
            // whose `detail` is pydantic's list of rows — reached the person
            // as raw JSON. `message` is the sentence the backend composes
            // beside the rows; a string `detail` still wins for everything else.
            val said = runCatching {
                val body = JSONObject(text)
                body.optString("message").ifBlank {
                    if (body.opt("detail") is String) body.optString("detail") else ""
                }
            }.getOrNull()
            throw ApiException(if (said.isNullOrBlank()) "HTTP $code" else said)
        }
    }
}

/** What the deployment can and cannot reach. */
data class OfflinePosture(val offline: Boolean,
                          val externalTransmissionPossible: Boolean,
                          val localDestinationsAllowed: String,
                          val guarantees: List<String>)
