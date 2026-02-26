# FMRO Android

Kotlin + Jetpack Compose client.

## Current Status

- Android project skeleton created
- App module with Compose dashboard placeholder
- Ready for API integration (`/api/v1/overview`, `/applications`, `/jobs`)

## Build (Android Studio)

1. Open `FMRO/android` in Android Studio
2. Sync Gradle
3. Run `app` on device/emulator

## CLI (if Gradle available)

```bash
cd android
gradle :app:assembleDebug
```

## Next Steps

1. Add Retrofit + Kotlinx serialization client
2. Replace sample dashboard data with backend API data
3. Add create/edit flow for applications and interview rounds
