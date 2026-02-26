# FMRO Android

Kotlin + Jetpack Compose client.

## Current Status

- Bottom navigation: Jobs / Pipeline / Settings
- Interactive Compose screens with clickable cards and dialogs
- API integration wired for `/api/v1/applications`, `/api/v1/jobs`, `/api/v1/companies`
- Jobs tab: keyword + city filters, bookmark (persisted), detail dialog, apply/source link jump
- Jobs tab supports crawler import trigger (with configurable import size)
- Pipeline tab: stage filter + quick actions + add form + delete application
- Settings tab: theme mode/language/endpoint/crawler-limit persisted locally, auto-update toggle, update check, one-click APK update, release jump
- Shows real backend data only; if backend is unreachable it displays an explicit error instead of fake demo jobs

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

1. Optionally migrate local persistence from SharedPreferences to DataStore
2. Add job detail page with richer fields (salary, tags, skill requirements)
3. Connect review queue management UI (approve/reject manually)
