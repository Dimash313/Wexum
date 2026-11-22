#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v gradle >/dev/null || { echo 'BLOCKED: Gradle 8.11.1 is not installed' >&2; exit 2; }
command -v javac >/dev/null || { echo 'BLOCKED: JDK 17 is required' >&2; exit 2; }
[[ "$(java -version 2>&1 | head -n1)" == *'17.'* ]] || { echo 'BLOCKED: run with JDK 17' >&2; exit 2; }
gradle_version="$(gradle --version | awk '/^Gradle / {print $2; exit}')"
[[ "$gradle_version" == '8.11.1' ]] || { echo "BLOCKED: Gradle 8.11.1 required, got $gradle_version" >&2; exit 2; }
: "${ANDROID_HOME:=${ANDROID_SDK_ROOT:-}}"
[[ -n "$ANDROID_HOME" && -d "$ANDROID_HOME/platforms/android-35" ]] || {
  echo 'BLOCKED: Android SDK platform 35 required' >&2
  exit 2
}
gradle --no-daemon --stacktrace :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
