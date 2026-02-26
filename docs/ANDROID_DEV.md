# Android Dev Loop (Ubuntu)

Yes, Ubuntu is fully supported for Android development.

## 1) Install tooling on Ubuntu

Choose one Android Studio install method:

```bash
# Option A: Snap
sudo snap install android-studio --classic
```

Or install from the official tarball:

- https://developer.android.com/studio

Then in Android Studio:
- Install Android SDK Platform + Build Tools
- Install Android Emulator
- Install one system image (recommended API 34, Google APIs x86_64)

## 2) Create/start emulator

In Android Studio:
- `Tools -> Device Manager -> Create device`
- Use a Pixel profile + API 34 image
- Start the emulator

## 3) Fast local loop (backend + app install)

From repo root:

```bash
./scripts/dev_android_loop.sh up emulator
```

What it does:
- Starts backend (if not already running)
- Waits for `http://127.0.0.1:8080/health`
- Builds debug APK
- Installs APK via `adb install -r`
- Launches `com.neomelt.fmro/.MainActivity`

For real phone (USB debug):

```bash
./scripts/dev_android_loop.sh up usb
```

This mode enables `adb reverse tcp:8080 tcp:8080`, so app can use host backend directly.

## 4) API endpoint mapping

- Emulator: `http://10.0.2.2:8080/`
- USB phone with `adb reverse`: `http://127.0.0.1:8080/`
- Custom endpoint (LAN):

```bash
FMRO_API_BASE_URL=http://192.168.1.8:8080/ ./scripts/dev_android_loop.sh up usb
```

## 5) Useful debug commands

```bash
# App logs
adb logcat | grep -i -E 'fmro|okhttp|retrofit|AndroidRuntime'

# Backend logs
tail -f .tmp/dev-android/backend.log

# Stop backend started by helper
./scripts/dev_android_loop.sh down
```
