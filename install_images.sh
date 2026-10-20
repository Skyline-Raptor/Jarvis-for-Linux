#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
bash install_media.sh
echo 'Examples are under docs/. Export your compatible ComfyUI workflow in API format.'
