package com.luiz.infostorage

import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

internal data class VaultRecord(
    val id: String,
    val title: String,
    val username: String,
    val password: String,
    val notes: String,
)

internal data class VaultNote(
    val id: String,
    val title: String,
    val content: String,
)

internal data class VaultContents(
    val credentials: List<VaultRecord>,
    val notes: List<VaultNote>,
)

internal fun parseVaultContents(data: JSONObject): VaultContents {
    val credentialsArray = data.optJSONArray("credentials") ?: JSONArray()
    val credentials = (0 until credentialsArray.length()).map { index ->
        val item = credentialsArray.getJSONObject(index)
        VaultRecord(
            id = item.getString("id").ifBlank { UUID.randomUUID().toString() },
            title = item.optString("title", "Sem nome"),
            username = item.optString("username"),
            password = item.optString("password"),
            notes = item.optString("notes"),
        )
    }

    val notesArray = data.optJSONArray("notes") ?: JSONArray()
    val notes = (0 until notesArray.length()).map { index ->
        val item = notesArray.getJSONObject(index)
        VaultNote(
            id = item.getString("id").ifBlank { UUID.randomUUID().toString() },
            title = item.optString("title", "Sem título"),
            content = item.optString("content"),
        )
    }

    return VaultContents(credentials, notes)
}
