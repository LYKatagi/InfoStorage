# 1. Preservar as classes de ponte e os métodos usados para comunicação com o Python
-keep class com.luiz.infostorage.PythonBridge { *; }
-keep class com.luiz.infostorage.PythonAppStatus { *; }

# 2. Preservar todas as classes de dados internas usadas na serialização/mapeamento JSON
-keep class com.luiz.infostorage.MainActivity$VaultRecord { *; }
-keep class com.luiz.infostorage.MainActivity$VaultNote { *; }

# 3. Manter os nomes dos métodos nativos e reflection intactos para o Chaquopy mapear
-keepattributes EnclosingMethod, InnerClasses, Signature, *Annotation*
-keepclassmembers class * {
    @androidx.compose.runtime.Composable *;
}
# Remove atributos de depuração de strings e linhas que inflam o binário
-assumenosideeffects class android.util.Log {
    public static boolean isLoggable(java.lang.String, int);
    public static int v(...);
    public static int d(...);
}

# Otimização agressiva de caminhos de execução do Kotlin
-repackageclasses ''
-allowaccessmodification
