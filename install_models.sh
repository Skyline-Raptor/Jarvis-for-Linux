#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
command -v ollama >/dev/null 2>&1 || { echo 'Install Ollama first using the steps in SETUP_STEP_BY_STEP.md. Official guide: https://docs.ollama.com/linux'; exit 1; }
export OLLAMA_NO_CLOUD=1
export OLLAMA_HOST=127.0.0.1:11434
ollama list >/dev/null || { echo 'Ollama is not reachable on its default local address. Start its service first.'; exit 1; }
# Each download resumes on rerun. These are local models, not :cloud models.
ollama pull qwen3:8b
ollama pull qwen2.5vl:3b
ollama pull nomic-embed-text
echo 'Models ready. For less memory use: ollama pull qwen3:4b; choose qwen3:4b in Jarvis Settings.'
