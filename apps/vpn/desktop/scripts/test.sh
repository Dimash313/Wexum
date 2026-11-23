#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cmake -S . -B build -DBUILD_TESTING=ON -DWEXUM_DESKTOP_BUILD_UI=OFF
cmake --build build --parallel 2
ctest --test-dir build --output-on-failure
