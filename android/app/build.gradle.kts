plugins {
    id("com.android.application")
    id("com.chaquo.python")
    id("org.jetbrains.kotlin.plugin.compose") // Adicione esta linha aqui

}



android {
    namespace = "com.luiz.infostorage"
    compileSdk {
        version = release(37)
    }

    defaultConfig {
        applicationId = "com.luiz.infostorage"
        minSdk = 24
        targetSdk = 37
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        ndk {
            abiFilters.addAll(setOf("arm64-v8a", "x86_64"))
        }

        
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            
            // CORREÇÃO: Passando os arquivos como argumentos da função (sem o "=")
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        compose = true
    }
}
// Certifique-se de que este bloco está bem no final do arquivo, FORA do bloco android { }


chaquopy {
    defaultConfig {
        version = "3.13"
        buildPython("uv", "run", "--no-project", "--python", "3.13", "python")
        pip {
            install("argon2-cffi")
            install("cryptography")
        }
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    testImplementation(libs.junit)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.junit)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
    debugImplementation(libs.androidx.compose.ui.tooling)
    implementation("androidx.biometric:biometric:1.2.0-alpha05")
}
