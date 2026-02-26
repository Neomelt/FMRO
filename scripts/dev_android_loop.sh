#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$ROOT_DIR/.tmp/dev-android"
PID_FILE="$TMP_DIR/backend.pid"
LOG_FILE="$TMP_DIR/backend.log"

mkdir -p "$TMP_DIR"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

resolve_gradle_cmd() {
  if [ -x "$ROOT_DIR/android/gradlew" ]; then
    echo "$ROOT_DIR/android/gradlew"
    return
  fi

  if command -v gradle >/dev/null 2>&1; then
    echo "gradle"
    return
  fi

  echo ""
}

backend_running() {
  if [ -f "$PID_FILE" ]; then
    local pid
    pid="$(cat "$PID_FILE")"
    if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
      return 0
    fi
  fi
  return 1
}

start_backend() {
  if backend_running; then
    echo "Backend already running (pid $(cat "$PID_FILE"))."
    return
  fi

  echo "Starting backend..."
  nohup "$ROOT_DIR/scripts/run_backend.sh" >"$LOG_FILE" 2>&1 &
  echo "$!" >"$PID_FILE"
}

wait_backend() {
  local retries=45
  local health_url="http://127.0.0.1:8080/health"

  for _ in $(seq 1 "$retries"); do
    if curl -fsS "$health_url" >/dev/null 2>&1; then
      echo "Backend healthy: $health_url"
      return
    fi
    sleep 1
  done

  echo "Backend health check failed after ${retries}s."
  if [ -f "$LOG_FILE" ]; then
    echo "---- backend log tail ----"
    tail -n 40 "$LOG_FILE" || true
    echo "--------------------------"
  fi
  exit 1
}

stop_backend() {
  if ! backend_running; then
    echo "Backend is not running."
    rm -f "$PID_FILE"
    return
  fi

  local pid
  pid="$(cat "$PID_FILE")"
  echo "Stopping backend pid $pid ..."
  kill "$pid" >/dev/null 2>&1 || true
  rm -f "$PID_FILE"
}

select_api_url() {
  local mode="$1"

  if [ -n "${FMRO_API_BASE_URL:-}" ]; then
    echo "$FMRO_API_BASE_URL"
    return
  fi

  if [ "$mode" = "usb" ]; then
    # For real devices, adb reverse makes 127.0.0.1 point to host port 8080.
    echo "http://127.0.0.1:8080/"
  else
    # For emulator, 10.0.2.2 maps to host localhost.
    echo "http://10.0.2.2:8080/"
  fi
}

ensure_device_online() {
  if ! adb get-state >/dev/null 2>&1; then
    echo "No Android device/emulator detected."
    echo "- Start an emulator from Android Studio Device Manager, or"
    echo "- Connect a real phone with USB debugging enabled."
    exit 1
  fi
}

install_debug_apk() {
  local api_url="$1"
  local mode="$2"
  local gradle_cmd="$3"

  if [ "$mode" = "usb" ]; then
    echo "Enabling adb reverse tcp:8080 -> host:8080"
    adb reverse tcp:8080 tcp:8080
  fi

  echo "Building debug APK with FMRO_API_BASE_URL=$api_url"
  if [ "$gradle_cmd" = "gradle" ]; then
    gradle -p "$ROOT_DIR/android" :app:assembleDebug -PfmroApiBaseUrl="$api_url"
  else
    "$gradle_cmd" -p "$ROOT_DIR/android" :app:assembleDebug -PfmroApiBaseUrl="$api_url"
  fi

  local apk="$ROOT_DIR/android/app/build/outputs/apk/debug/app-debug.apk"
  if [ ! -f "$apk" ]; then
    echo "APK not found: $apk"
    exit 1
  fi

  echo "Installing APK..."
  adb install -r "$apk"
  adb shell am start -n com.neomelt.fmro/.MainActivity >/dev/null

  echo "Done."
  echo "Useful commands:"
  echo "- Logs: adb logcat | grep -i -E 'fmro|okhttp|retrofit|AndroidRuntime'"
  echo "- Backend log: tail -f $LOG_FILE"
}

usage() {
  cat <<EOF
FMRO Android dev loop helper

Usage:
  ./scripts/dev_android_loop.sh up [emulator|usb]
  ./scripts/dev_android_loop.sh down

Examples:
  ./scripts/dev_android_loop.sh up emulator
  ./scripts/dev_android_loop.sh up usb
  FMRO_API_BASE_URL=http://192.168.1.8:8080/ ./scripts/dev_android_loop.sh up usb
  ./scripts/dev_android_loop.sh down

Notes:
- 'up emulator' uses API base URL http://10.0.2.2:8080/
- 'up usb' enables adb reverse and uses http://127.0.0.1:8080/
- Set SKIP_BACKEND=1 if backend is already running
EOF
}

main() {
  local action="${1:-up}"

  case "$action" in
    up)
      local mode="${2:-emulator}"
      if [ "$mode" != "emulator" ] && [ "$mode" != "usb" ]; then
        echo "Invalid mode: $mode"
        usage
        exit 1
      fi

      require_cmd adb
      require_cmd curl

      local gradle_cmd
      gradle_cmd="$(resolve_gradle_cmd)"
      if [ -z "$gradle_cmd" ]; then
        echo "Missing Gradle runtime. Install Gradle or add android/gradlew."
        exit 1
      fi

      if [ "${SKIP_BACKEND:-0}" != "1" ]; then
        start_backend
      fi
      wait_backend
      ensure_device_online

      local api_url
      api_url="$(select_api_url "$mode")"
      install_debug_apk "$api_url" "$mode" "$gradle_cmd"
      ;;

    down)
      stop_backend
      ;;

    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
