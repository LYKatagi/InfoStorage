package com.luiz.infostorage

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun LocalLockPlaceholder() {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Mist),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            CircularProgressIndicator(color = Green)
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Aguardando autenticação do sistema...",
                color = Muted,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium
            )
        }
    }
}
