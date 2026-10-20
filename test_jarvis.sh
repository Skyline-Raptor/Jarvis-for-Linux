#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
.venv/bin/python scripts/run_tests.py
QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/ui_smoke.py
