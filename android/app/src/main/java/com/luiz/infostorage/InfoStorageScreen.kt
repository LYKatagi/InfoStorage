package com.luiz.infostorage

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
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
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

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
    var activeSection by rememberSaveable { mutableStateOf("credentials") }
    var vaultNotes by remember { mutableStateOf(listOf<VaultNote>()) }
    var addingNote by rememberSaveable { mutableStateOf(false) }
    var noteTitle by rememberSaveable { mutableStateOf("") }
    var noteContent by rememberSaveable { mutableStateOf("") }
    var syncMode by rememberSaveable { mutableStateOf(false) }
    var createApiAccount by rememberSaveable { mutableStateOf(false) }
    var apiUsername by rememberSaveable { mutableStateOf("") }
    var apiUrl by rememberSaveable { mutableStateOf(bridge.savedApiUrl()) }

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
                    vaultNotes = emptyList()
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

    fun loadVaultData(): String =
        if (syncMode) bridge.syncLoadData(apiUrl) else bridge.loadData()

    fun saveVaultData(data: String): String =
        if (syncMode) bridge.syncSaveData(apiUrl, data) else bridge.saveData(data)

    fun applyVaultData(result: JSONObject) {
        result.optJSONObject("data")?.let { data ->
            val contents = parseVaultContents(data)
            records = contents.credentials
            vaultNotes = contents.notes
        }
    }

    LaunchedEffect(Unit) { refreshStatus() }

    val createAccount = if (syncMode) createApiAccount else accountExists == false
    val screenTitle = when {
        syncMode && createApiAccount -> "Novo cofre sincronizado"
        syncMode -> "Conectar ao seu cofre"
        createAccount -> "Seu espaço privado"
        else -> "Bem-vindo de volta"
    }

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
if (accountExists == null) {
Box(modifier = Modifier.fillMaxWidth().weight(1f), contentAlignment = Alignment.Center) {
CircularProgressIndicator(color = Green)
}
} else if (!unlocked) {
Row(modifier = Modifier.fillMaxWidth().padding(bottom = 22.dp)) {
Button(
onClick = { syncMode = false; password = ""; confirmPassword = ""; notice = null },
modifier = Modifier.weight(1f).height(42.dp),
shape = RoundedCornerShape(10.dp),
colors = ButtonDefaults.buttonColors(containerColor = if (!syncMode) Green else Color.Transparent),
) {
Text("Somente local", color = if (!syncMode) Color.White else Ink, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
}
Button(
onClick = { syncMode = true; password = ""; confirmPassword = ""; notice = null },
modifier = Modifier.weight(1f).height(42.dp),
shape = RoundedCornerShape(10.dp),
colors = ButtonDefaults.buttonColors(containerColor = if (syncMode) Green else Color.Transparent),
) {
Text("Sincronizar API", color = if (syncMode) Color.White else Ink, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
}
}
Text("ÁREA SEGURA", color = Green, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
Spacer(Modifier.height(6.dp))
Text(screenTitle, color = Ink, fontSize = 26.sp, fontWeight = FontWeight.Bold)
Spacer(Modifier.height(8.dp))
Text(
when {
    syncMode && createApiAccount -> "Crie uma conta para manter o cofre sincronizado com a API."
    syncMode -> "Entre na conta remota para carregar seus dados sincronizados."
    createAccount -> "Crie uma senha forte para encriptar suas informações."
    else -> "Insira sua senha mestra para abrir o cofre."
},
color = Muted, fontSize = 14.sp
)
if (syncMode) {
Spacer(Modifier.height(18.dp))
OutlinedTextField(
value = apiUrl,
onValueChange = { apiUrl = it; bridge.saveApiUrl(it) },
label = { Text("URL da API") },
placeholder = { Text("https://seu-servidor") },
keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri, imeAction = ImeAction.Next),
modifier = Modifier.fillMaxWidth(),
singleLine = true,
)
Spacer(Modifier.height(12.dp))
OutlinedTextField(
value = apiUsername,
onValueChange = { apiUsername = it },
label = { Text("Usuário da API") },
keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text, imeAction = ImeAction.Next),
modifier = Modifier.fillMaxWidth(),
singleLine = true,
)
}
Spacer(Modifier.height(28.dp))
OutlinedTextField(
value = password,
onValueChange = { password = it },
label = { Text("Senha Mestra") },
visualTransformation = PasswordVisualTransformation(),
keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = ImeAction.Next),
modifier = Modifier.fillMaxWidth(),
singleLine = true
)
if (createAccount) {
Spacer(Modifier.height(16.dp))
OutlinedTextField(
value = confirmPassword,
onValueChange = { confirmPassword = it },
label = { Text("Confirme a Senha") },
visualTransformation = PasswordVisualTransformation(),
keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = ImeAction.Done),
modifier = Modifier.fillMaxWidth(),
singleLine = true
)
}
Spacer(Modifier.height(24.dp))
Button(
onClick = {
if (syncMode) {
if (createApiAccount && password != confirmPassword) {
notice = "As senhas não coincidem." to true
return@Button
}
bridge.saveApiUrl(apiUrl)
val syncAction = if (createApiAccount) {
{ bridge.syncRegister(apiUrl, apiUsername, password) }
} else {
{ bridge.syncLogin(apiUrl, apiUsername, password) }
}
runAction(syncAction) { result ->
password = ""
confirmPassword = ""
unlocked = true
val data = result.optJSONObject("data")
if (data != null) {
val contents = parseVaultContents(data)
records = contents.credentials
vaultNotes = contents.notes
}
}
} else if (createAccount) {
if (password != confirmPassword) {
notice = "As senhas não coincidem." to true
return@Button
}
runAction({ bridge.register(password) }) {
password = ""
confirmPassword = ""
refreshStatus()
}
} else if (!vaultExists) {
runAction({ bridge.createVault(password) }) { res ->
password = ""
unlocked = true
records = emptyList()
vaultNotes = emptyList()
}
} else {
runAction({ bridge.login(password) }) { res ->
password = ""
unlocked = true
val innerData = res.optJSONObject("data")
if (innerData != null) {
val contents = parseVaultContents(innerData)
records = contents.credentials
vaultNotes = contents.notes
}
}
}
},
modifier = Modifier.fillMaxWidth().height(48.dp),
colors = ButtonDefaults.buttonColors(containerColor = Green),
shape = RoundedCornerShape(12.dp),
enabled = !busy && password.isNotEmpty() &&
    (!syncMode || apiUsername.isNotBlank()) &&
    (!createAccount || confirmPassword.isNotEmpty())
) {
if (busy) CircularProgressIndicator(color = Color.White, modifier = Modifier.size(20.dp))
else Text(
when {
    syncMode && createApiAccount -> "Criar e sincronizar"
    syncMode -> "Entrar e sincronizar"
    createAccount -> "Criar espaço local"
    !vaultExists -> "Criar cofre local"
    else -> "Desbloquear local"
},
fontWeight = FontWeight.Bold,
)
}
if (syncMode) {
TextButton(
onClick = { createApiAccount = !createApiAccount; password = ""; confirmPassword = "" },
modifier = Modifier.fillMaxWidth(),
) {
Text(if (createApiAccount) "Já tem uma conta? Entrar" else "Criar nova conta sincronizada", color = Green)
}
}
notice?.let { (msg, isErr) ->
Spacer(Modifier.height(16.dp))
Text(msg, color = if (isErr) Error else Green, fontSize = 13.sp, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth())
}
} else {
// VIEW UNLOCKED COFRE
Text("ÁREA SEGURA", color = Green, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
Spacer(Modifier.height(6.dp))
Text("Seu cofre", color = Ink, fontSize = 26.sp, fontWeight = FontWeight.Bold)
Spacer(Modifier.height(8.dp))
Text("Credenciais e anotações protegidas em um só lugar.", color = Muted, fontSize = 14.sp)
Text(
    if (syncMode) "Sincronizado com a API" else "Armazenado somente neste dispositivo",
    color = Green,
    fontSize = 12.sp,
    fontWeight = FontWeight.SemiBold,
    modifier = Modifier.padding(top = 6.dp),
)
Spacer(Modifier.height(24.dp))
// ABAS SELETORAS
Card(
modifier = Modifier.fillMaxWidth(),
colors = CardDefaults.cardColors(containerColor = Color.White),
shape = RoundedCornerShape(14.dp),
border = BorderStroke(1.dp, Line)
) {
Row(modifier = Modifier.padding(4.dp)) {
Button(
onClick = { activeSection = "credentials"; addingRecord = false; addingNote = false; editingRecordId = null },
modifier = Modifier.weight(1f).height(40.dp),
colors = ButtonDefaults.buttonColors(containerColor = if (activeSection == "credentials") Green else Color.Transparent),
shape = RoundedCornerShape(11.dp),
elevation = null
) {
Text("Credenciais ${records.size}", color = if (activeSection == "credentials") Color.White else Ink, fontSize = 13.sp, fontWeight = FontWeight.Bold)
}
Button(
onClick = { activeSection = "notes"; addingRecord = false; addingNote = false; editingRecordId = null },
modifier = Modifier.weight(1f).height(40.dp),
colors = ButtonDefaults.buttonColors(containerColor = if (activeSection == "notes") Green else Color.Transparent),
shape = RoundedCornerShape(11.dp),
elevation = null
) {
Text("Notas ${vaultNotes.size}", color = if (activeSection == "notes") Color.White else Ink, fontSize = 13.sp, fontWeight = FontWeight.Bold)
}
}
}
Spacer(Modifier.height(24.dp))
if (!addingRecord && editingRecordId == null && !addingNote) {
Row(verticalAlignment = Alignment.CenterVertically) {
Column {
Text("ITENS SALVOS", color = Muted, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.1.sp)
Text(
if (activeSection == "credentials") "${records.size} ${if (records.size == 1) "credencial" else "credenciais"}"
else "${vaultNotes.size} ${if (vaultNotes.size == 1) "anotação" else "anotações"}",
color = Ink, fontSize = 18.sp, fontWeight = FontWeight.Bold
)
Spacer(Modifier.height(4.dp))
TextButton(
onClick = {
runAction(::loadVaultData, ::applyVaultData)
},
contentPadding = PaddingValues(0.dp),
colors = ButtonDefaults.textButtonColors(contentColor = Muted)
) {
Text("↻ Atualizar lista", fontSize = 12.sp)
}
}
Spacer(Modifier.weight(1f))
Button(
onClick = {
if (activeSection == "credentials") addingRecord = true else addingNote = true
title = ""; username = ""; secret = ""; notes = ""; noteTitle = ""; noteContent = ""
},
colors = ButtonDefaults.buttonColors(containerColor = Ink),
shape = RoundedCornerShape(10.dp),
contentPadding = PaddingValues(horizontal = 14.dp, vertical = 8.dp)
) {
Text("+ Novo item", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
}
}
Spacer(Modifier.height(16.dp))
notice?.let { (msg, isErr) ->
Text(msg, color = if (isErr) Error else Green, fontSize = 13.sp, modifier = Modifier.padding(bottom = 12.dp))
}
if (activeSection == "credentials") {
if (records.isEmpty()) {
Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(12.dp), border = BorderStroke(1.dp, Line)) {
Text("Nenhuma credencial salva.", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(24.dp).fillMaxWidth(), textAlign = TextAlign.Center)
}
} else {
records.forEach { item ->
Card(
modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp),
colors = CardDefaults.cardColors(containerColor = Color.White),
shape = RoundedCornerShape(12.dp),
border = BorderStroke(1.dp, Line)
) {
Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
Surface(shape = RoundedCornerShape(8.dp), color = Mist, modifier = Modifier.size(36.dp)) {
Box(contentAlignment = Alignment.Center) {
Text(item.title.take(1).uppercase(), color = Green, fontWeight = FontWeight.Bold, fontSize = 14.sp)
}
}
Spacer(Modifier.width(12.dp))
Column(modifier = Modifier.weight(1f)) {
Text(item.title, color = Ink, fontSize = 14.sp, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
Text(item.username, color = Muted, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
if (item.notes.isNotEmpty()) {
Text(item.notes, color = Muted, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
}
Text("••••••••", color = Muted, fontSize = 11.sp)
}
Row {
TextButton(onClick = {
editingRecordId = item.id
title = item.title
username = item.username
secret = item.password
notes = item.notes
}) {
Text("Editar", color = Green, fontSize = 12.sp)
}
TextButton(onClick = {
val updated = records.filter { it.id != item.id }
val root = JSONObject().apply {
val cArr = JSONArray()
updated.forEach { r ->
cArr.put(JSONObject().apply { put("id", r.id); put("title", r.title); put("username", r.username); put("password", r.password); put("notes", r.notes) })
}
put("credentials", cArr)
val nArr = JSONArray()
vaultNotes.forEach { n ->
nArr.put(JSONObject().apply { put("id", n.id); put("title", n.title); put("content", n.content) })
}
put("notes", nArr)
}
runAction({ saveVaultData(root.toString()) }, ::applyVaultData)
}) {
Text("Remover", color = Error, fontSize = 12.sp)
}
}
}
}
}
}
} else {
// SEÇÃO NOTAS
if (vaultNotes.isEmpty()) {
Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(12.dp), border = BorderStroke(1.dp, Line)) {
Text("Nenhuma anotação salva.", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(24.dp).fillMaxWidth(), textAlign = TextAlign.Center)
}
} else {
vaultNotes.forEach { note ->
Card(
modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp),
colors = CardDefaults.cardColors(containerColor = Color.White),
shape = RoundedCornerShape(12.dp),
border = BorderStroke(1.dp, Line)
) {
Column(modifier = Modifier.padding(14.dp)) {
Row(verticalAlignment = Alignment.CenterVertically) {
Surface(shape = RoundedCornerShape(8.dp), color = Color(0xFFE8EFFC), modifier = Modifier.size(36.dp)) {
Box(contentAlignment = Alignment.Center) {
Text("N", color = Color(0xFF3C78B4), fontWeight = FontWeight.Bold, fontSize = 14.sp)
}
}
Spacer(Modifier.width(12.dp))
Column(modifier = Modifier.weight(1f)) {
Text(note.title, color = Ink, fontSize = 14.sp, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
}
TextButton(onClick = {
val updated = vaultNotes.filter { it.id != note.id }
val root = JSONObject().apply {
val cArr = JSONArray()
records.forEach { r ->
cArr.put(JSONObject().apply { put("id", r.id); put("title", r.title); put("username", r.username); put("password", r.password); put("notes", r.notes) })
}
put("credentials", cArr)
val nArr = JSONArray()
updated.forEach { n ->
nArr.put(JSONObject().apply { put("id", n.id); put("title", n.title); put("content", n.content) })
}
put("notes", nArr)
}
runAction({ saveVaultData(root.toString()) }, ::applyVaultData)
}) {
Text("Remover", color = Error, fontSize = 12.sp)
}
}
Spacer(Modifier.height(8.dp))
Text(note.content, color = Muted, fontSize = 13.sp)
}
}
}
}
}
Spacer(Modifier.height(24.dp))
HorizontalDivider(color = Line)
Spacer(Modifier.height(14.dp))
OutlinedButton(
onClick = {
runAction({ if (syncMode) bridge.syncLogout(apiUrl) else bridge.logout() }) {
unlocked = false
records = emptyList()
vaultNotes = emptyList()
}
},
modifier = Modifier.fillMaxWidth().height(44.dp),
shape = RoundedCornerShape(10.dp),
border = BorderStroke(1.dp, Line),
colors = ButtonDefaults.outlinedButtonColors(contentColor = Error)
) {
Text("Trancar Cofre", fontWeight = FontWeight.Bold, fontSize = 13.sp)
}
} else if (addingRecord || editingRecordId != null) {
// FORMULÁRIO DE CREDENCIAIS
Text(if (addingRecord) "NOVA CREDENCIAL" else "EDITAR CREDENCIAL", color = Green, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.1.sp)
Spacer(Modifier.height(16.dp))
OutlinedTextField(value = title, onValueChange = { title = it }, label = { Text("Nome do Serviço / App") }, modifier = Modifier.fillMaxWidth(), singleLine = true, keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Words))
Spacer(Modifier.height(12.dp))
OutlinedTextField(value = username, onValueChange = { username = it }, label = { Text("Usuário / E-mail") }, modifier = Modifier.fillMaxWidth(), singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email))
Spacer(Modifier.height(12.dp))
OutlinedTextField(value = secret, onValueChange = { secret = it }, label = { Text("Senha") }, modifier = Modifier.fillMaxWidth(), singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password))
Spacer(Modifier.height(12.dp))
OutlinedTextField(value = notes, onValueChange = { notes = it }, label = { Text("Anotações adicionais") }, modifier = Modifier.fillMaxWidth(), maxLines = 3)
Spacer(Modifier.height(20.dp))
Row {
OutlinedButton(
onClick = { addingRecord = false; editingRecordId = null },
modifier = Modifier.weight(1f).height(46.dp),
shape = RoundedCornerShape(10.dp),
border = BorderStroke(1.dp, Line),
colors = ButtonDefaults.outlinedButtonColors(contentColor = Ink)
) {
Text("Cancelar", fontSize = 13.sp)
}
Spacer(Modifier.width(12.dp))
Button(
onClick = {
val targetId = editingRecordId ?: UUID.randomUUID().toString()
val currentList = if (editingRecordId != null) records.filter { it.id != editingRecordId } else records
val updatedList = currentList + VaultRecord(targetId, title, username, secret, notes)
val root = JSONObject().apply {
val cArr = JSONArray()
updatedList.forEach { r ->
cArr.put(JSONObject().apply { put("id", r.id); put("title", r.title); put("username", r.username); put("password", r.password); put("notes", r.notes) })
}
put("credentials", cArr)
val nArr = JSONArray()
vaultNotes.forEach { n ->
nArr.put(JSONObject().apply { put("id", n.id); put("title", n.title); put("content", n.content) })
}
put("notes", nArr)
}
runAction({ saveVaultData(root.toString()) }) { result ->
applyVaultData(result)
addingRecord = false
editingRecordId = null
}
},
modifier = Modifier.weight(1f).height(46.dp),
shape = RoundedCornerShape(10.dp),
colors = ButtonDefaults.buttonColors(containerColor = Green),
enabled = title.isNotEmpty() && username.isNotEmpty() && secret.isNotEmpty()
) {
Text("Salvar", fontWeight = FontWeight.Bold, fontSize = 13.sp)
}
}
} else if (addingNote) {
// FORMULÁRIO DE NOTAS
Text("NOVA ANOTAÇÃO SECRETA", color = Green, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.1.sp)
Spacer(Modifier.height(16.dp))
OutlinedTextField(value = noteTitle, onValueChange = { noteTitle = it }, label = { Text("Título da Nota") }, modifier = Modifier.fillMaxWidth(), singleLine = true, keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Sentences))
Spacer(Modifier.height(12.dp))
OutlinedTextField(value = noteContent, onValueChange = { noteContent = it }, label = { Text("Conteúdo da Anotação") }, modifier = Modifier.fillMaxWidth(), minLines = 5)
Spacer(Modifier.height(20.dp))
Row {
OutlinedButton(
onClick = { addingNote = false },
modifier = Modifier.weight(1f).height(46.dp),
shape = RoundedCornerShape(10.dp),
border = BorderStroke(1.dp, Line),
colors = ButtonDefaults.outlinedButtonColors(contentColor = Ink)
) {
Text("Cancelar", fontSize = 13.sp)
}
Spacer(Modifier.width(12.dp))
Button(
onClick = {
val newNote = VaultNote(UUID.randomUUID().toString(), noteTitle, noteContent)
val updatedList = vaultNotes + newNote
val root = JSONObject().apply {
val cArr = JSONArray()
records.forEach { r ->
cArr.put(JSONObject().apply { put("id", r.id); put("title", r.title); put("username", r.username); put("password", r.password); put("notes", r.notes) })
}
put("credentials", cArr)
val nArr = JSONArray()
updatedList.forEach { n ->
nArr.put(JSONObject().apply { put("id", n.id); put("title", n.title); put("content", n.content) })
}
put("notes", nArr)
}
runAction({ saveVaultData(root.toString()) }) { result ->
applyVaultData(result)
addingNote = false
}
},
modifier = Modifier.weight(1f).height(46.dp),
shape = RoundedCornerShape(10.dp),
colors = ButtonDefaults.buttonColors(containerColor = Green),
enabled = noteTitle.isNotEmpty() && noteContent.isNotEmpty()
) {
Text("Salvar Nota", fontWeight = FontWeight.Bold, fontSize = 13.sp)
}
}
}
}
Spacer(Modifier.height(32.dp))
}
}
