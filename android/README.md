# FMRO Android

Kotlin + Jetpack Compose client.

## Current Status

- Bottom navigation: Jobs / Pipeline / Settings
- Interactive Pipeline dashboard (stage filter, quick actions, add form)
- API integration wired for `/api/v1/applications`, `/api/v1/jobs`, `/api/v1/companies`
- Jobs tab supports crawler import trigger and apply/source link jump
- Settings tab supports theme mode, language mode, update check and release jump
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
