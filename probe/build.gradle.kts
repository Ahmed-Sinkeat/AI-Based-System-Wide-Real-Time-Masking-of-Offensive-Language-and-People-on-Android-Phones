buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:2.4.10") } // pins the Kotlin compiler AGP's built-in Kotlin uses (cached)
}

plugins { id("com.android.application") version "9.3.1" }

android {
    namespace = "dev.masking.probe"
    compileSdk = 36
    defaultConfig {
        applicationId = "dev.masking.probe"
        minSdk = 34 // takeScreenshotOfWindow needs Android 14
        targetSdk = 36
        versionCode = 1
        versionName = "0.1"
    }
}
