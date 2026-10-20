# Jarvis Fresh Linux Mint — validation report

Release: **1.0.1-preview.1-linux**, 20 October 2026.

The complete existing preview was ported to Linux, with new shell installers,
XDG data/menu/autostart paths, explicit Secret Service credential storage,
Cinnamon/GNOME/XFCE screen-lock checks, X11 foreground capture, Wayland refusal
for desktop observation/control, asynchronous secure-service connection/retry,
launcher reactivation, and reviewed Linux source activation with backup.

A defect found during testing was fixed: a missing/broken PortAudio import during
Stop could prevent text chat from submitting. Text-only installations now work
without the optional voice stack. Credential operations also serialize chunked
read/write/delete access so simultaneous callers cannot race a cache replacement.

## Environment and reproducibility

- Ubuntu 24.04.3 Linux environment, x86_64, glibc 2.39, CPython 3.12.14.
- This was **not a clean Linux Mint Cinnamon desktop installation**.
- A clean full runtime was installed entirely from the bundled Linux wheelhouse,
  with package-index access disabled. All **109 runtime distributions** installed.
- A second clean text-only runtime was installed from the same wheelhouse. Its
  full regression suite and UI smoke test passed without Kokoro, Whisper or sounddevice.
- **110 wheels** are bundled: the runtime set plus uv 0.13.4 for bootstrapping.
  Python, apt libraries, Ollama and model weights remain separate downloads.
- A pinned Linux dependency lock, source, tests, logs, seven UI screenshots and
  two generated audio samples are included. `release-manifest.json` records file
  hashes; `python3 scripts/verify_release.py` checks immutable package consistency.
  This receipt is not a publisher signature or independent security certification.

## Final regression runs

The final application changes passed **125 tests** in each of three consecutive
runs, with **zero failures, zero errors and zero skips**:

| Final run | Tests | Failures / errors / skips | Duration |
|---|---:|---|---:|
| 1 | 125 | 0 / 0 / 0 | 10.210 s |
| 2 | 125 | 0 / 0 / 0 | 9.243 s |
| 3 | 125 | 0 / 0 / 0 | 9.479 s |

These are `linux-final-round-2`, `-3`, `-4` under test-results. Earlier development
runs, including the original 95-test baseline and an intermediate 114-test suite,
are retained separately and are not added to the final test count.

Coverage includes real filesystem conflict detection/backups, Office/PDF round
trips, SQLite memory and reminders, approved command subprocesses, local simulated
HTTP model/media endpoints, real local TLS pairing and resumable file transfers,
and policy/credential boundary cases. Linux additions cover private data paths,
permissions, X11/Wayland selection, unknown/timeout/locked screensaver responses,
foreground bounds and exclusions, capture race discarding, autostart file lifecycle,
missing audio resilience, explicit secure-backend failure and candidate activation.

Candidate activation was exercised in temporary installations: a passing candidate
replaces complete source folders and produces a readable backup; failed candidate
tests and cancelled application leave the installed source unchanged. This is not
a simulation of power loss halfway through filesystem replacement.

## UI and audio

- **Three final offscreen Qt UI simulations passed**, each checking window creation,
  streamed scripted conversation, completion buttons, memory/settings, all seven
  pages, literal text rendering, asynchronous locked-keyring failure, retry wiring
  through account/tools/scheduler/device objects, and close/hide/reopen behavior.
  Model responses and keyring availability were simulated in this UI test.
- **Two real voice pipeline runs passed** using downloaded Kokoro assets,
  `bm_george`, ONNX Runtime, and local Whisper `small.en` on CPU.
  Each produced 4.693 seconds of **24,000 Hz** audio and transcribed:
  “Hello, this is Jarvis. Your local voice system is ready for testing.”
  Their measured end-to-end times were 10.67 s and 8.41 s in this environment.
  No live microphone or speakers were used.
- All **nine shell launch/install/check/update scripts** passed `bash -n`.
  Python source compiled successfully. Installer help and refusal to launch/install
  as root were also exercised; the full sudo/apt desktop installer was not run as
  a normal Mint user here.
- `pip-audit` scanned the pinned **109 runtime dependencies** and found **zero known
  advisories** at scan time. Its JSON result is included. This is not a source-code
  security audit or assurance that no unknown vulnerabilities exist.

## Native checks still required on your Mint machine

The build environment disallows native desktop Unix sockets. The isolated Xvfb /
D-Bus harness could not establish its desktop listener, so **native X11 capture,
actual Cinnamon lock state, desktop pointer/keyboard control, Secret Service
round trips, tray behavior, local launcher socket and autostart are unverified**.
The refusal/failure log is retained as `test-results/linux-native.log`; it is not
a passing native test. Privacy logic and those boundaries have unit/simulation
coverage, as described above.

Also unverified here: actual Mint 21 managed-Python bootstrap, NVIDIA drivers and
real Qwen GPU inference, live microphone/playback/wake accuracy, Google/Microsoft
OAuth and provider operations with your accounts, real ComfyUI generation/video,
sleep/resume behavior and transfers between actual machines over your VPN.
Mocked provider/model tests and single-host TLS tests do not establish these.

Start with `SETUP_STEP_BY_STEP.md`; then run `bash test_jarvis.sh` and, after local
models and voice assets are installed, `bash native_check.sh`. Manually test the
above desktop/hardware features before relying on background operation.

## Retained feature limits

This release ports the existing engineering preview. It does not add previously
missing autonomous phone calling, global keyboard push-to-talk, automatic shared
memory/conversation sync, unattended remote execution, universal document fidelity,
a hostile-code sandbox, signed updates or Obsidian integration. Local model quality
is separate from transport/runtime correctness. Tests reduce defects; they do not
establish that the project is bug-free.
