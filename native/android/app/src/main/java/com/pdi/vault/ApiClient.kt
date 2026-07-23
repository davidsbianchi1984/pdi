package com.pdi.vault

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

// MARK: wire models (mirror pdi/api.py)

data class VaultRecord(val key: String, val value: String, val updatedAt: String?)
data class AuditEntry(val seq: Int, val action: String, val ref: String?, val at: String, val category: String?)

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
}
