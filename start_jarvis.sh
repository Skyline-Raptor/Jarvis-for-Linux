#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if (( EUID == 0 )); then echo 'Start Jarvis as your normal desktop user, not root.' >&2; exit 1; fi
[[ -x .venv/bin/python ]] || { echo 'First run: bash install.sh' >&2; exit 1; }
if [[ -z ${DISPLAY:-} && -z ${WAYLAND_DISPLAY:-} ]]; then echo 'Start Jarvis from a terminal in your graphical desktop session.' >&2; exit 1; fi
export OLLAMA_NO_CLOUD=1
state="${JARVIS_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/jarvis-fresh}"
mkdir -p -- "$state"; chmod 700 -- "$state"
# Keep the launcher alive so failures from menu launches are visible.
set +e
.venv/bin/python -m jarvis "$@" >> "$state/runtime.log" 2>&1
result=$?
set -e
if (( result != 0 )); then
  echo "Jarvis exited with status $result. Read: $state/runtime.log" >&2
  if command -v zenity >/dev/null 2>&1; then zenity --error --text="Jarvis could not start. Read $state/runtime.log" || true; fi
fi
exit "$result"
