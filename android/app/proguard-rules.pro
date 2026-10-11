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
