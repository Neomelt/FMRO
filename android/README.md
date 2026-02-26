# FMRO Android

Kotlin + Jetpack Compose client.

## Current Status

- Android project skeleton created
- Interactive Compose dashboard (stage filter, quick actions, add form)
- API integration wired for `/api/v1/applications`
- Falls back to demo data when backend is unreachable

## Build (Android Studio)

1. Open `FMRO/android` in Android Studio
2. Sync Gradle
3. Ensure backend is running (`http://10.0.2.2:8080` from emulator)
4. Run `app` on device/emulator

## CLI (if Gradle available)

```bash
cd android
gradle :app:assembleDebug
```

## Next Steps

1. Add Retrofit + Kotlinx serialization client
2. Replace sample dashboard data with backend API data
3. Add create/edit flow for applications and interview rounds
