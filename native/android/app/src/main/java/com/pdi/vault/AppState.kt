package com.pdi.vault

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import kotlinx.coroutines.launch

/**
 * App-wide state: the tenant bearer token + base URL (persisted to
 * SharedPreferences) and the async calls the screens invoke.
 */
class VaultViewModel(app: Application) : AndroidViewModel(app) {
    private val prefs = app.getSharedPreferences("pdi", 0)

    var token by mutableStateOf<String?>(prefs.getString("token", null))
        private set
    var baseURL by mutableStateOf(prefs.getString("base", "http://10.0.2.2:8000") ?: "http://10.0.2.2:8000")
        private set

    init { ApiClient.setBase(baseURL) }

    val isSignedIn get() = token != null

    /** Validate the pasted token against GET /records, then persist on success. */
    fun signIn(token: String, base: String, onError: (String) -> Unit, onBusy: (Boolean) -> Unit) {
        onBusy(true)
        ApiClient.setBase(base)
        viewModelScope.launch {
            runCatching { ApiClient.keys(token) }
                .onSuccess { _ ->
                    this@VaultViewModel.token = token
                    this@VaultViewModel.baseURL = base
                    prefs.edit().putString("token", token).putString("base", base).apply()
                }
                .onFailure { onError(it.message ?: "Couldn't unlock — check the token and server.") }
            onBusy(false)
        }
    }

    fun signOut() {
        token = null
        prefs.edit().remove("token").apply()
    }

    fun <T> call(block: suspend () -> T, onResult: (Result<T>) -> Unit) {
        viewModelScope.launch { onResult(runCatching { block() }) }
    }
}
