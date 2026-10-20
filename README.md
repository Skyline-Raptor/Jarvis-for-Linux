# Jarvis Fresh — Linux Mint edition

## Install from GitHub

Download **Code → Download ZIP** and extract it, or clone this repository:

```bash
git clone https://github.com/Skyline-Raptor/Jarvis-for-Linux.git
cd Jarvis-for-Linux
bash install.sh
```

Run as your normal desktop user. Install Ollama and run `bash install_models.sh`,
then `bash start_jarvis.sh`. Use Cinnamon/X11 for screen awareness and desktop control.
Follow [SETUP_STEP_BY_STEP.md](SETUP_STEP_BY_STEP.md) for the complete procedure.

This GitHub source edition downloads pinned Python dependencies from PyPI.
An optional complete `wheelhouse/` cache enables offline Python package installation.
Ollama and model weights install separately. See [GITHUB_IMPORT.md](GITHUB_IMPORT.md)
for provenance and the small installer changes made for this repository.

Version **1.0.1-preview.1-linux**, ported from the Windows 1.0.0 preview.

Read **SETUP_STEP_BY_STEP.md** first. Extract this folder to a permanent location,
open a terminal there, and run `bash install.sh` as your normal desktop user.
Install Ollama and run `bash install_models.sh`, then `bash start_jarvis.sh`.
The installer includes voice by default; `--skip-voice` defers its downloads.

Target: Linux Mint 22.x, x86_64, Cinnamon/X11. Mint 21.x has a managed Python 3.12
bootstrap path but has not been tested here. The core UI, files and chat can run
under Wayland; screen awareness and desktop control require X11 in this port.

All existing Python modules are included: chat/tools, files and Office/PDF creation,
memory, accounts, scheduling, George/Whisper voice, paired TLS transfers, screen
awareness, ComfyUI/FFmpeg adapters, and reviewed improvement staging. This is a
port of the existing engineering preview, not an implementation of previously
missing features. Phone calling, automatic memory sync, and Obsidian are absent.
See FEATURE_STATUS.md and TEST_REPORT.md for exact verification boundaries.

Linux additions include per-user shell installation and launch, XDG directories,
Secret Service credential storage without plaintext fallback, Cinnamon lock-state
checks, X11 foreground capture, menu/autostart entries, launcher reactivation,
and a source-candidate backup/rollback helper. Archived Windows scripts are
reference material under docs/original-windows; do not run those for Linux.

The optional Linux wheelhouse supports the pinned Python dependencies for CPython
3.12 x86_64; the GitHub source edition uses PyPI when that cache is absent. apt packages, Python itself, Ollama and model weights need separate
installation/download. Full source and tests are included. No personal credentials
or live account data are distributed. Commands execute with your user permissions.
