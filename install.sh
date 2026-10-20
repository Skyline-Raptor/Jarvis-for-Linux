#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
skip_system=0; voice=1; models=0
for arg in "$@"; do
  case "$arg" in
    --skip-system) skip_system=1;;
    --skip-voice) voice=0;;
    --with-models) models=1;;
    --help) echo 'bash install.sh [--skip-system] [--skip-voice] [--with-models]'; exit 0;;
    *) echo "Unknown option: $arg" >&2; exit 2;;
  esac
done
if (( EUID == 0 )); then echo 'Run this as your normal desktop user, without sudo. It will request sudo only for system packages.' >&2; exit 1; fi
[[ $(uname -m) == x86_64 ]] || { echo 'This release targets Linux x86_64.' >&2; exit 1; }
mkdir -p install-logs
log="install-logs/install-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$log") 2>&1
trap 'echo "Installation stopped at line $LINENO. Read $log, fix the reported error, and run this installer again."' ERR
if (( ! skip_system )); then
  sudo apt-get update
  sudo apt-get install -y python3 python3-venv python3-tk ca-certificates curl zstd \
    libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-xinerama0 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 \
    libportaudio2 libsndfile1 gnome-keyring dbus-x11 libglib2.0-bin xclip scrot ffmpeg desktop-file-utils
fi
# Private bootstrap and application environments. Never install packages into distro Python.
python3 -m venv .bootstrap
package_source=()
if compgen -G 'wheelhouse/*.whl' > /dev/null; then
  package_source=(--no-index --find-links wheelhouse)
  echo 'Using the local offline wheel cache.'
else
  echo 'GitHub source edition: downloading pinned Python packages from PyPI.'
fi
.bootstrap/bin/python -m pip install --disable-pip-version-check "${package_source[@]}" 'uv==0.13.4' 
UV="$PWD/.bootstrap/bin/uv"
if [[ ! -x .venv/bin/python ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    "$UV" venv --python "$(command -v python3.12)" .venv
  else
    # Mint 21's system Python is 3.10. Use a separate managed 3.12 interpreter.
    "$UV" python install 3.12
    "$UV" venv --python 3.12 --managed-python .venv
  fi
fi
.venv/bin/python -c 'import sys; assert sys.version_info[:2]==(3,12), "Remove .venv and rerun: Python 3.12 is required by this bundle"'
req=(-r requirements.txt)
if (( voice )); then req+=(-r requirements-voice.txt); fi
"$UV" pip install --python .venv/bin/python "${package_source[@]}" -c requirements-linux.lock "${req[@]}"
"$UV" pip freeze --python .venv/bin/python > resolved-environment.txt
.venv/bin/python scripts/run_tests.py
.venv/bin/python scripts/setup_desktop.py
if (( voice )); then .venv/bin/python scripts/download_voice.py; fi
if (( models )); then bash install_models.sh; fi
echo 'Jarvis installed. Start it with: bash start_jarvis.sh'
echo 'AI models: bash install_models.sh (Ollama must be installed first; see SETUP_STEP_BY_STEP.md).'
echo 'If keyring services are unavailable, log out and back in, then use Accounts → Connect / retry.'
