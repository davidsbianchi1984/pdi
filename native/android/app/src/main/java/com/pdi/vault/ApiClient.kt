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
data class AuditEntry(val seq: Int, val action: String, val ref: String?, val at: String, val category: String?)
data class RobotSpec(val model: String, val label: String, val maker: String)
data class Robot(val id: String, val model: String, val name: String, val status: String?, val collected: Int)
data class IngestResult(val sealed: Boolean, val key: String)
data class ComplianceProgram(val key: String, val label: String)
data class Transfer(val id: String, val recipient: String, val filename: String,
                    val status: String, val programs: List<String>,
                    val expiresAt: String?, val receiveToken: String?)
data class Intake(val id: String, val fromParty: String, val purpose: String?,
                  val status: String, val programs: List<String>,
                  val filename: String?, val submitToken: String?)
data class IntakeFile(val filename: String?, val content: String?)
data class SocialConn(val id: String, val platform: String, val direction: String,
                      val handle: String?, val status: String?)

class ApiException(message: String) : Exception(message)

/**
 * Coroutine client for the PDI vault backend. Every call carries the tenant
 * bearer token (`pdi_...`), issued out of band and pasted at sign-in.
 *
 * The Android emulator reaches the host machine at 10.0.2.2, so that is the
 * default. On a physical device, set your machine's LAN IP via [base].
 */
object ApiClient {
    @Volatile var base: String = "http://10.0.2.2:8000"

    fun setBase(url: String) {
        val t = url.trimEnd('/')
        if (t.isNotBlank()) base = t
    }

    private suspend fun request(
        path: String, method: String = "GET",
        body: JSONObject? = null, token: String,
    ): String = withContext(Dispatchers.IO) {
        val conn = (URL(base + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            setRequestProperty("content-type", "application/json")
            setRequestProperty("authorization", "Bearer $token")
            connectTimeout = 8000; readTimeout = 8000
            if (body != null) {
                doOutput = true
                outputStream.use { it.write(body.toString().toByteArray()) }
            }
        }
        val code = conn.responseCode
        val text = (if (code in 200..299) conn.inputStream else conn.errorStream)
            ?.bufferedReader()?.use { it.readText() } ?: ""
        conn.disconnect()
        if (code !in 200..299) {
            val detail = runCatching { JSONObject(text).optString("detail") }.getOrNull()
            throw ApiException(if (detail.isNullOrBlank()) "HTTP $code" else detail)
        }
        text
    }

    /** List record keys — also the sign-in validation call. */
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

    suspend fun language(token: String): String {
        return JSONObject(request("/language", token = token)).getString("language")
    }

    suspend fun setLanguage(token: String, code: String) {
        request("/language", "PUT", JSONObject().put("language", code), token)
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
        return IngestResult(o.optBoolean("sealed"), o.getString("key"))
    }

    suspend fun robotKeys(token: String, rid: String): List<String> {
        val arr = JSONObject(request("/robots/$rid/data", token = token))
            .getJSONArray("keys")
        return (0 until arr.length()).map { arr.getString(it) }
    }

    // ---- compliance-grade secure transfers ----

    private fun transferOf(o: JSONObject): Transfer {
        val progs = o.optJSONArray("programs")
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
        val progs = o.optJSONArray("programs")
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
            val detail = runCatching { JSONObject(text).optString("detail") }.getOrNull()
            throw ApiException(if (detail.isNullOrBlank()) "HTTP $code" else detail)
        }
    }
}
