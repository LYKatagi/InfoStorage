package com.luiz.infostorage

import android.content.Context
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONObject

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

    fun logout(): String {
        return app.callAttr(
            "logout_json"
        ).toString()
    }
}