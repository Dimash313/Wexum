plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.ihsansoft.wexumvpn"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.ihsansoft.wexumvpn"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "dev"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
}
