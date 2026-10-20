#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -x .bootstrap/bin/uv && -x .venv/bin/python ]] || { echo 'Run bash install.sh first.'; exit 1; }
package_source=()
if compgen -G 'wheelhouse/*.whl' > /dev/null; then
  package_source=(--no-index --find-links wheelhouse)
fi
.bootstrap/bin/uv pip install --python .venv/bin/python "${package_source[@]}" -r requirements-voice.txt -c requirements-linux.lock
.venv/bin/python scripts/download_voice.py
.bootstrap/bin/uv pip freeze --python .venv/bin/python > resolved-environment.txt
echo 'Voice assets installed. Test with: .venv/bin/python scripts/voice_smoke.py'
