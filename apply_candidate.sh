#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
.venv/bin/python scripts/apply_candidate.py "$@"
