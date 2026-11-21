#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
swift test
if command -v plutil >/dev/null 2>&1; then
  plutil -lint -s -- WexumVPN.xcodeproj/project.pbxproj WexumVPNApp/WexumVPNApp.entitlements
fi
if ! command -v xcodebuild >/dev/null 2>&1; then
  echo 'BLOCKED: Xcode project compilation requires a macOS runner with Xcode.' >&2
  exit 78
fi
xcodebuild -project WexumVPN.xcodeproj -scheme WexumVPN -sdk iphonesimulator -configuration Debug CODE_SIGNING_ALLOWED=NO build
