package com.luiz.infostorage

import android.app.KeyguardManager
import android.content.Context
import android.os.Bundle
import android.view.WindowManager
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

class MainActivity : ComponentActivity() {

    private var isDeviceAuthenticated by mutableStateOf(false)

    private val unlockLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            isDeviceAuthenticated = true
            Toast.makeText(this, "Acesso liberado ao cofre!", Toast.LENGTH_SHORT).show()
        } else {
            isDeviceAuthenticated = false
            Toast.makeText(this, "Autenticação necessária para prosseguir.", Toast.LENGTH_LONG).show()
            requestDeviceUnlock()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Impede prints, gravações de tela e esconde o app nos recentes
        window.setFlags(
            WindowManager.LayoutParams.FLAG_SECURE,
            WindowManager.LayoutParams.FLAG_SECURE
        )

        val bridge = PythonBridge(this)
        requestDeviceUnlock()

        setContent {
            MaterialTheme {
                if (isDeviceAuthenticated) {
                    InfoStorageScreen(bridge)
                } else {
                    LocalLockPlaceholder()
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        if (!isDeviceAuthenticated) {
            requestDeviceUnlock()
        }
    }

    override fun onPause() {
        super.onPause()
        isDeviceAuthenticated = false
    }

    private fun requestDeviceUnlock() {
        val keyguardManager = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
        if (keyguardManager.isKeyguardSecure) {
            val intent = keyguardManager.createConfirmDeviceCredentialIntent(
                "InfoStorage Protegido",
                "Confirme o padrão ou PIN de desbloqueio para acessar suas credenciais."
            )
            if (intent != null) {
                unlockLauncher.launch(intent)
            } else {
                isDeviceAuthenticated = true
            }
        } else {
            isDeviceAuthenticated = true
        }
    }
}
