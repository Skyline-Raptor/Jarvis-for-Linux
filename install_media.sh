#!/usr/bin/env bash
set -Eeuo pipefail
sudo apt-get update
sudo apt-get install -y ffmpeg
ffmpeg -version | head -n 1 || true
echo 'Optional images/video require a separate ComfyUI installation and compatible models.'
echo 'Official Linux instructions: https://docs.comfy.org/installation/manual_install'
echo 'Run it on http://127.0.0.1:8188 and select an API workflow in Jarvis Settings.'
