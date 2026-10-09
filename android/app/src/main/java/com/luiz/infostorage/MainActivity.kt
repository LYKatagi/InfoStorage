package com.luiz.infostorage

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.foundation.BorderStroke
import androidx.compose.material3.HorizontalDivider
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.foundation.layout.PaddingValues
import org.json.JSONArray
import org.json.JSONObject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.UUID

private val Ink = Color(0xFF13221F)
private val Green = Color(0xFF176B55)
private val Mist = Color(0xFFF3F7F4)
private val Muted = Color(0xFF65736D)
private val Line = Color(0xFFE0E9E3)
private val Error = Color(0xFFB43C3C)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val bridge = PythonBridge(this)
        setContent {
            MaterialTheme {
                InfoStorageScreen(bridge)
            }
        }
    }
}

private data class VaultRecord(
    val id: String,
    val title: String,
    val username: String,
    val password: String,
    val notes: String,
)

@Composable
fun InfoStorageScreen(bridge: PythonBridge) {
    val scope = rememberCoroutineScope()
    var accountExists by rememberSaveable { mutableStateOf<Boolean?>(null) }
    var vaultExists by rememberSaveable { mutableStateOf(false) }
    var unlocked by remember { mutableStateOf(false) }
    var records by remember { mutableStateOf(listOf<VaultRecord>()) }
    var password by rememberSaveable { mutableStateOf("") }
    var confirmPassword by rememberSaveable { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var notice by remember { mutableStateOf<Pair<String, Boolean>?>(null) }
    var addingRecord by rememberSaveable { mutableStateOf(false) }
    var editingRecordId by rememberSaveable { mutableStateOf<String?>(null) }
    var title by rememberSaveable { mutableStateOf("") }
    var username by rememberSaveable { mutableStateOf("") }
    var secret by rememberSaveable { mutableStateOf("") }
    var notes by rememberSaveable { mutableStateOf("") }

    fun runAction(action: () -> String, onSuccess: (JSONObject) -> Unit = {}) {
        if (busy) return
        scope.launch {
            busy = true
            notice = null
            try {
                val result = withContext(Dispatchers.IO) { JSONObject(action()) }
                val success = result.optBoolean("success", false)
                val message = result.optString("message", "Operação concluída.")
                notice = message to !success
                if (success) onSuccess(result)
                else if (result.optBoolean("requires_login")) {
                    unlocked = false
                    records = emptyList()
                }
            } catch (error: Exception) {
                notice = (error.message ?: "Não foi possível concluir a operação.") to true
            } finally {
                busy = false
            }
        }
    }

    fun refreshStatus() {
        if (busy) return
        scope.launch {
            busy = true
            notice = null
            try {
                val status = withContext(Dispatchers.IO) { bridge.getStatus() }
                accountExists = status.credentialsExist
                vaultExists = status.vaultExists
                unlocked = status.unlocked
            } catch (error: Exception) {
                notice = (error.message ?: "Não foi possível consultar o status.") to true
            } finally {
                busy = false
            }
        }
    }

    LaunchedEffect(Unit) { refreshStatus() }

    val createAccount = accountExists == false
    val screenTitle = if (createAccount) "Seu espaço privado" else "Bem-vindo de volta"

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Mist)
            .statusBarsPadding()
            .navigationBarsPadding()
            .imePadding()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 22.dp),
    ) {
        Spacer(Modifier.height(24.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Surface(shape = RoundedCornerShape(17.dp), color = Green, modifier = Modifier.size(48.dp)) {
                Box(contentAlignment = Alignment.Center) {
                    Text("IS", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 17.sp)
                }
            }
            Spacer(Modifier.width(12.dp))
            Column {
                Text("INFOSTORAGE", color = Ink, fontSize = 14.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.6.sp)
                Text("Seu cofre, só seu.", color = Muted, fontSize = 12.sp)
            }
            Spacer(Modifier.weight(1f))
            if (unlocked) {
                Surface(color = Color(0xFFE1F1E8), shape = CircleShape) {
                    Text("●  PROTEGIDO", color = Green, fontSize = 10.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 11.dp, vertical = 8.dp))
                }
            }
        }

        Spacer(Modifier.height(32.dp))
        if (unlocked) {
            Text("ÁREA SEGURA", color = Green, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.5.sp)
            Spacer(Modifier.height(8.dp))
            Text("Suas credenciais", color = Ink, fontSize = 29.sp, fontWeight = FontWeight.Bold)
            Text("Tudo organizado e protegido em um só lugar.", color = Muted, fontSize = 14.sp, modifier = Modifier.padding(top = 5.dp))
            Spacer(Modifier.height(22.dp))
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(22.dp),
                border = BorderStroke(1.dp, Line),
            ) {
                Column(Modifier.fillMaxWidth().padding(18.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("ITENS SALVOS", color = Muted, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                            Text("${records.size} ${if (records.size == 1) "credencial" else "credenciais"}", color = Ink, fontSize = 20.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 4.dp))
                        }
                        Button(
                            onClick = {
                                if (addingRecord) {
                                    addingRecord = false
                                    editingRecordId = null
                                } else {
                                    editingRecordId = null
                                    title = ""; username = ""; secret = ""; notes = ""
                                    addingRecord = true
                                }
                            },
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Green),
                            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
                        ) { Text(if (addingRecord) "Fechar" else "+  Novo item", fontSize = 13.sp) }
                    }
                    TextButton(
                        onClick = {
                            runAction(bridge::loadData) { result -> records = parseRecords(result.optJSONArray("data")) }
                        },
                        modifier = Modifier.padding(top = 4.dp),
                    ) { Text("↻  Atualizar lista", color = Green, fontSize = 12.sp) }
                    if (addingRecord) {
                        HorizontalDivider(color = Line, modifier = Modifier.padding(vertical = 16.dp))
                        Text(if (editingRecordId == null) "Adicionar credencial" else "Editar credencial", color = Ink, fontSize = 17.sp, fontWeight = FontWeight.SemiBold)
                        Spacer(Modifier.height(12.dp))
                        AppField(title, { title = it }, "Nome do serviço", keyboard = KeyboardCapitalization.Sentences)
                        Spacer(Modifier.height(10.dp))
                        AppField(username, { username = it }, "Usuário ou e-mail")
                        Spacer(Modifier.height(10.dp))
                        AppField(secret, { secret = it }, "Senha", isSecret = true)
                        Spacer(Modifier.height(10.dp))
                        AppField(notes, { notes = it }, "Observações (opcional)", keyboard = KeyboardCapitalization.Sentences, singleLine = false)
                        Spacer(Modifier.height(14.dp))
                        Button(
                            enabled = !busy && title.isNotBlank() && secret.isNotBlank(),
                            onClick = {
                                val changedRecord = VaultRecord(editingRecordId ?: UUID.randomUUID().toString(), title.trim(), username.trim(), secret, notes.trim())
                                val updated = if (editingRecordId == null) records + changedRecord else records.map { if (it.id == editingRecordId) changedRecord else it }
                                runAction({ bridge.saveData(serializeRecords(updated)) }) { result ->
                                    records = parseRecords(result.optJSONArray("data"))
                                    title = ""; username = ""; secret = ""; notes = ""; addingRecord = false; editingRecordId = null
                                }
                            },
                            modifier = Modifier.fillMaxWidth().height(50.dp),
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Green),
                        ) { Text(if (busy) "Salvando…" else if (editingRecordId == null) "Salvar no cofre" else "Salvar alterações", fontWeight = FontWeight.SemiBold) }
                    }
                }
            }
            Spacer(Modifier.height(14.dp))
            if (records.isEmpty()) {
                Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(20.dp), border = BorderStroke(1.dp, Line)) {
                    Column(Modifier.fillMaxWidth().padding(horizontal = 22.dp, vertical = 28.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("✦", color = Green, fontSize = 28.sp)
                        Spacer(Modifier.height(8.dp))
                        Text("Seu cofre está pronto", color = Ink, fontWeight = FontWeight.SemiBold, fontSize = 17.sp)
                        Text("Adicione o primeiro acesso para começar.", color = Muted, fontSize = 13.sp, textAlign = TextAlign.Center, modifier = Modifier.padding(top = 5.dp))
                    }
                }
            } else {
                records.forEach { record ->
                    RecordCard(
                        record = record,
                        onEdit = {
                            editingRecordId = record.id
                            title = record.title; username = record.username; secret = record.password; notes = record.notes
                            addingRecord = true
                        },
                        onDelete = {
                            val updated = records.filterNot { it.id == record.id }
                            runAction({ bridge.saveData(serializeRecords(updated)) }) { result -> records = parseRecords(result.optJSONArray("data")) }
                        },
                    )
                    Spacer(Modifier.height(10.dp))
                }
            }
            Spacer(Modifier.height(16.dp))
            OutlinedButton(
                onClick = {
                    runAction(bridge::logout) {
                        unlocked = false; records = emptyList(); password = ""; confirmPassword = ""; addingRecord = false
                    }
                },
                modifier = Modifier.fillMaxWidth().height(52.dp),
                shape = RoundedCornerShape(15.dp),
                border = BorderStroke(1.dp, Line),
            ) { Text("Bloquear cofre", color = Ink, fontWeight = FontWeight.SemiBold) }
        } else {
            Text("SEGURANÇA SIMPLES, NO SEU CONTROLE", color = Green, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
            Spacer(Modifier.height(10.dp))
            Text(if (accountExists == null) "Preparando seu cofre" else screenTitle, color = Ink, fontSize = 30.sp, lineHeight = 36.sp, fontWeight = FontWeight.Bold)
            Text(
                if (createAccount) "Crie uma senha principal para proteger suas informações." else "Entre com sua senha principal para acessar suas informações.",
                color = Muted, fontSize = 14.sp, lineHeight = 21.sp, modifier = Modifier.padding(top = 8.dp)
            )
            Spacer(Modifier.height(22.dp))
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(24.dp),
                border = BorderStroke(1.dp, Line),
            ) {
                Column(Modifier.fillMaxWidth().padding(20.dp)) {
                    Text(if (createAccount) "Criar conta" else "Login", color = Ink, fontSize = 19.sp, fontWeight = FontWeight.SemiBold)
                    Text(if (createAccount) "Uma senha forte mantém seus dados privados." else "Sua senha nunca sai deste dispositivo.", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 4.dp, bottom = 18.dp))
                    AppField(password, { password = it }, "Senha principal", isSecret = true)
                    if (createAccount) {
                        Spacer(Modifier.height(11.dp))
                        AppField(confirmPassword, { confirmPassword = it }, "Confirmar senha", isSecret = true)
                    }
                    Spacer(Modifier.height(16.dp))
                    Button(
                        enabled = accountExists != null && !busy && password.isNotEmpty() && (!createAccount || confirmPassword.isNotEmpty()),
                        onClick = {
                            if (createAccount && password != confirmPassword) {
                                notice = "As senhas não coincidem." to true
                            } else if (createAccount) {
                                runAction({
                                    val registration = JSONObject(bridge.register(password))
                                    if (registration.optBoolean("success")) bridge.createVault(password) else registration.toString()
                                }) { result ->
                                    unlocked = true; vaultExists = true; records = parseRecords(result.optJSONArray("data")); password = ""; confirmPassword = ""
                                }
                            } else {
                                runAction({ if (vaultExists) bridge.login(password) else bridge.createVault(password) }) { result ->
                                    unlocked = true; vaultExists = true; records = parseRecords(result.optJSONArray("data")); password = ""
                                }
                            }
                        },
                        modifier = Modifier.fillMaxWidth().height(54.dp),
                        shape = RoundedCornerShape(15.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Green),
                    ) {
                        if (busy) CircularProgressIndicator(Modifier.size(19.dp), color = Color.White, strokeWidth = 2.dp)
                        else Text(if (createAccount) "Criar conta e cofre" else "Fazer login", fontWeight = FontWeight.SemiBold)
                    }
                    if (accountExists == true) {
                        TextButton(onClick = { refreshStatus() }, modifier = Modifier.align(Alignment.CenterHorizontally)) { Text("Atualizar status", color = Muted) }
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFE9F1EC)), shape = RoundedCornerShape(18.dp)) {
                Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.Top) {
                    Text("⌑", color = Green, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    Spacer(Modifier.width(11.dp))
                    Column {
                        Text("Protegido no dispositivo", color = Ink, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                        Text("Seus dados ficam em um cofre criptografado e são desbloqueados com sua senha.", color = Muted, fontSize = 12.sp, lineHeight = 17.sp, modifier = Modifier.padding(top = 3.dp))
                    }
                }
            }
        }

        notice?.let { (message, isError) ->
            Spacer(Modifier.height(14.dp))
            Surface(color = if (isError) Color(0xFFFFEBE9) else Color(0xFFE3F2E9), shape = RoundedCornerShape(14.dp)) {
                Text(message, color = if (isError) Error else Green, fontSize = 13.sp, modifier = Modifier.fillMaxWidth().padding(14.dp))
            }
        }
        Spacer(Modifier.height(24.dp))
        Text("INFOSTORAGE  ·  PRIVACIDADE EM PRIMEIRO LUGAR", color = Muted, fontSize = 9.sp, letterSpacing = 0.7.sp, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp))
    }
}

@Composable
private fun AppField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    isSecret: Boolean = false,
    keyboard: KeyboardCapitalization? = null,
    singleLine: Boolean = true,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = Modifier.fillMaxWidth(),
        label = { Text(label) },
        singleLine = singleLine,
        minLines = if (singleLine) 1 else 3,
        visualTransformation = if (isSecret) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = KeyboardOptions(
            keyboardType = if (isSecret) KeyboardType.Password else KeyboardType.Text,
            capitalization = keyboard ?: KeyboardCapitalization.None,
            imeAction = if (singleLine) ImeAction.Next else ImeAction.Default,
        ),
        shape = RoundedCornerShape(14.dp),
        colors = androidx.compose.material3.OutlinedTextFieldDefaults.colors(
            focusedBorderColor = Green,
            focusedLabelColor = Green,
            cursorColor = Green,
        ),
    )
}

@Composable
private fun RecordCard(record: VaultRecord, onEdit: () -> Unit, onDelete: () -> Unit) {
    var showPassword by remember(record.id) { mutableStateOf(false) }
    Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(18.dp), border = BorderStroke(1.dp, Line)) {
        Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.Top) {
            Surface(color = Color(0xFFE8F2EC), shape = RoundedCornerShape(13.dp), modifier = Modifier.size(42.dp)) {
                Box(contentAlignment = Alignment.Center) { Text(record.title.take(1).uppercase(), color = Green, fontWeight = FontWeight.Bold, fontSize = 17.sp) }
            }
            Spacer(Modifier.width(13.dp))
            Column(Modifier.weight(1f)) {
                Text(record.title, color = Ink, fontSize = 16.sp, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                if (record.username.isNotBlank()) Text(record.username, color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 3.dp), maxLines = 1, overflow = TextOverflow.Ellipsis)
                if (record.notes.isNotBlank()) Text(record.notes, color = Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 6.dp), maxLines = 2, overflow = TextOverflow.Ellipsis)
                Text(if (showPassword) record.password else "••••••••", color = Green, fontSize = 13.sp, letterSpacing = if (showPassword) 0.sp else 1.3.sp, modifier = Modifier.padding(top = 8.dp))
                Row {
                    TextButton(onClick = { showPassword = !showPassword }) { Text(if (showPassword) "Ocultar" else "Mostrar senha", color = Green, fontSize = 12.sp) }
                    TextButton(onClick = onEdit) { Text("Editar", color = Ink, fontSize = 12.sp) }
                }
            }
            TextButton(onClick = onDelete) { Text("Remover", color = Error, fontSize = 12.sp) }
        }
    }
}

private fun serializeRecords(records: List<VaultRecord>): String = JSONArray().apply {
    records.forEach { record ->
        put(JSONObject().apply {
            put("id", record.id)
            put("title", record.title)
            put("username", record.username)
            put("password", record.password)
            put("notes", record.notes)
        })
    }
}.toString()

private fun parseRecords(array: JSONArray?): List<VaultRecord> {
    if (array == null) return emptyList()
    return (0 until array.length()).mapNotNull { index ->
        val item = array.optJSONObject(index) ?: return@mapNotNull null
        VaultRecord(
            id = item.optString("id").ifBlank { UUID.randomUUID().toString() },
            title = item.optString("title", "Sem nome"),
            username = item.optString("username"),
            password = item.optString("password"),
            notes = item.optString("notes"),
        )
    }
}
