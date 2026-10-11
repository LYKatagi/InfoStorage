package com.luiz.infostorage

import android.content.Context
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.io.BufferedReader
import java.net.HttpURLConnection
import java.net.URI
import java.net.URL
import org.json.JSONArray
import org.json.JSONObject
import org.json.JSONTokener

private class APIResponseException(message: String, val statusCode: Int) :
    IllegalStateException(message)

data class PythonAppStatus(
    val credentialsExist: Boolean,
    val vaultExists: Boolean,
    val unlocked: Boolean,
)

class PythonBridge(
    context: Context
) {
    private val python: Python
    private val app: com.chaquo.python.PyObject
    private val preferences = context.getSharedPreferences("sync_settings", Context.MODE_PRIVATE)

    @Volatile
    private var apiToken: String? = null

    init {
        if (!Python.isStarted()) {
            Python.start(
                AndroidPlatform(context)
            )
        }

        python = Python.getInstance()

        val module = python.getModule(
            "info_storage.mobile_api"
        )

        val baseDir = context.filesDir.absolutePath

        app = module.callAttr(
            "InfoStorageApp",
            baseDir
        )
    }

    fun getStatus(): PythonAppStatus {
        val status = JSONObject(app.callAttr("get_status_json").toString())
        return PythonAppStatus(
            credentialsExist = status.optBoolean("account_exists"),
            vaultExists = status.optBoolean("vault_exists"),
            unlocked = status.optBoolean("unlocked"),
        )
    }

    fun register(password: String): String {
        return app.callAttr(
            "register_json",
            password
        ).toString()
    }

    fun createVault(password: String): String {
        return app.callAttr(
            "create_vault_json",
            password
        ).toString()
    }

    fun login(password: String): String {
        return app.callAttr(
            "login_json",
            password
        ).toString()
    }

    fun loadData(): String {
        return app.callAttr(
            "load_data_json"
        ).toString()
    }

    fun saveData(dataJson: String): String {
        return app.callAttr(
            "save_data_json",
            dataJson
        ).toString()
    }

    fun addNote(noteJson: String): String {
        return app.callAttr("add_note_json", noteJson).toString()
    }

    fun getNotes(): String {
        return app.callAttr("get_notes_json").toString()
    }

    fun logout(): String {
        return app.callAttr(
            "logout_json"
        ).toString()
    }

    fun savedApiUrl(): String = preferences.getString("api_url", DEFAULT_API_URL) ?: DEFAULT_API_URL

    fun saveApiUrl(apiUrl: String) {
        preferences.edit().putString("api_url", apiUrl.trim().trimEnd('/')).apply()
    }

    fun syncRegister(apiUrl: String, username: String, password: String): String =
        authenticateWithApi(apiUrl, "/api/v1/auth/register", username, password)

    fun syncLogin(apiUrl: String, username: String, password: String): String =
        authenticateWithApi(apiUrl, "/api/v1/auth/login", username, password)

    fun syncLoadData(apiUrl: String): String = apiResult {
        val token = requireApiToken()
        successResult("Dados sincronizados.", fetchRemoteData(apiUrl, token))
    }

    fun syncSaveData(apiUrl: String, dataJson: String): String = apiResult {
        val token = requireApiToken()
        val requested = JSONObject(dataJson)
        val remote = fetchRemoteData(apiUrl, token)
        val credentials = syncCollection(
            apiUrl,
            token,
            "credentials",
            requested.optJSONArray("credentials") ?: JSONArray(),
            remote.optJSONArray("credentials") ?: JSONArray(),
        )
        val notes = syncCollection(
            apiUrl,
            token,
            "notes",
            requested.optJSONArray("notes") ?: JSONArray(),
            remote.optJSONArray("notes") ?: JSONArray(),
        )
        successResult(
            "Alterações sincronizadas.",
            JSONObject().put("credentials", credentials).put("notes", notes),
        )
    }

    fun syncLogout(apiUrl: String): String {
        val token = apiToken ?: return successResult("Sessão encerrada.").toString()
        return try {
            apiRequest(apiUrl, "/api/v1/auth/logout", "POST", token)
            successResult("Sessão encerrada.").toString()
        } catch (error: Exception) {
            failureResult(error).toString()
        } finally {
            apiToken = null
        }
    }

    private fun authenticateWithApi(
        apiUrl: String,
        route: String,
        username: String,
        password: String,
    ): String = apiResult {
        validateApiUrl(apiUrl)
        val response = apiRequest(
            apiUrl,
            route,
            "POST",
            body = JSONObject().put("username", username).put("password", password),
        )
        val token = response.getString("access_token")
        apiToken = token
        try {
            successResult(
                "Sessão sincronizada.",
                fetchRemoteData(apiUrl, token),
            )
        } catch (error: Exception) {
            apiToken = null
            throw error
        }
    }

    private fun fetchRemoteData(apiUrl: String, token: String): JSONObject {
        val credentials = apiRequest(apiUrl, "/api/v1/credentials", "GET", token)
            .optJSONArray("data") ?: JSONArray()
        val notes = apiRequest(apiUrl, "/api/v1/notes", "GET", token)
            .optJSONArray("data") ?: JSONArray()
        return JSONObject().put("credentials", credentials).put("notes", notes)
    }

    private fun syncCollection(
        apiUrl: String,
        token: String,
        collection: String,
        requested: JSONArray,
        remote: JSONArray,
    ): JSONArray {
        val remoteItems = (0 until remote.length()).map { remote.getJSONObject(it) }
        val remoteById = remoteItems.associateBy { it.getString("id") }
        val retainedRemoteIds = mutableSetOf<String>()
        val synced = JSONArray()

        for (index in 0 until requested.length()) {
            val item = requested.getJSONObject(index)
            val itemId = item.optString("id")
            val payload = JSONObject(item.toString()).apply { remove("id") }
            val response = if (remoteById.containsKey(itemId)) {
                retainedRemoteIds.add(itemId)
                apiRequest(apiUrl, "/api/v1/$collection/$itemId", "PUT", token, payload)
            } else {
                apiRequest(apiUrl, "/api/v1/$collection", "POST", token, payload)
            }
            synced.put(response.getJSONObject("data"))
        }

        for (item in remoteItems) {
            val remoteId = item.getString("id")
            if (remoteId !in retainedRemoteIds &&
                (0 until requested.length()).none {
                    requested.getJSONObject(it).optString("id") == remoteId
                }
            ) {
                apiRequest(apiUrl, "/api/v1/$collection/$remoteId", "DELETE", token)
            }
        }
        return synced
    }

    private fun apiRequest(
        apiUrl: String,
        path: String,
        method: String,
        token: String? = null,
        body: JSONObject? = null,
    ): JSONObject {
        validateApiUrl(apiUrl)
        val normalizedBase = apiUrl.trim().trimEnd('/')
        val connection = URL("$normalizedBase$path").openConnection() as HttpURLConnection
        connection.requestMethod = method
        connection.connectTimeout = API_TIMEOUT_MS
        connection.readTimeout = API_TIMEOUT_MS
        connection.setRequestProperty("Accept", "application/json")
        if (token != null) connection.setRequestProperty("Authorization", "Bearer $token")
        if (body != null) {
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
        }

        try {
            val status = connection.responseCode
            if (status == HttpURLConnection.HTTP_NO_CONTENT) return JSONObject()
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val responseText = stream?.bufferedReader(Charsets.UTF_8)?.use(BufferedReader::readText).orEmpty()
            val response = when (val parsed = JSONTokener(responseText).nextValue()) {
                is JSONObject -> parsed
                is JSONArray -> JSONObject().put("data", parsed)
                else -> JSONObject()
            }
            if (status !in 200..299) {
                if (status == HttpURLConnection.HTTP_UNAUTHORIZED) apiToken = null
                throw APIResponseException(
                    response.optString("detail", "Falha na API ($status)."),
                    status,
                )
            }
            return response
        } finally {
            connection.disconnect()
        }
    }

    private fun validateApiUrl(apiUrl: String) {
        val uri = URI(apiUrl.trim())
        val host = uri.host?.lowercase() ?: throw IllegalArgumentException("Informe uma URL válida para a API.")
        val localDevelopmentHost = host in setOf("10.0.2.2", "127.0.0.1", "localhost")
        if (uri.scheme != "https" && !(uri.scheme == "http" && localDevelopmentHost)) {
            throw IllegalArgumentException("Use HTTPS. HTTP só é permitido no emulador local (10.0.2.2).")
        }
        if (uri.userInfo != null || uri.query != null || uri.fragment != null) {
            throw IllegalArgumentException("A URL da API não pode conter usuário, query ou fragmento.")
        }
    }

    private fun requireApiToken(): String =
        apiToken ?: throw IllegalStateException("Entre novamente na conta sincronizada.")

    private inline fun apiResult(action: () -> JSONObject): String = try {
        action().toString()
    } catch (error: Exception) {
        failureResult(error).toString()
    }

    private fun successResult(message: String, data: JSONObject? = null): JSONObject =
        JSONObject().put("success", true).put("message", message).apply {
            if (data != null) put("data", data)
        }

    private fun failureResult(error: Exception): JSONObject = JSONObject()
            .put("success", false)
            .put("message", error.message ?: "Não foi possível conectar à API.")
            .apply {
                if (error is APIResponseException &&
                    error.statusCode == HttpURLConnection.HTTP_UNAUTHORIZED
                ) {
                    put("requires_login", true)
                }
            }

    private companion object {
        const val API_TIMEOUT_MS = 12_000
        const val DEFAULT_API_URL = "http://10.0.2.2:8000"
    }
}