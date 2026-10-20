# Validation report — Jarvis Fresh 1.0.0-preview.1

Validation performed in the provided Linux/Python 3.12 workspace. Calendar date
in the user's requirements session: October 16, 2026. Machine-generated UTC run
timestamps are retained in the raw reports. This is not a native Windows release
certification, penetration test or guarantee of zero defects.

## Final checks

| Check | Result | What it establishes |
|---|---|---|
| Final regression suite, run 1 | 95 tests passed | Tested core behavior on this host |
| Final regression suite, run 2 | 95 tests passed | Repeated execution with independent temporary state |
| Final regression suite, run 3 | 95 tests passed | Third repeat; 95 distinct tests, 285 successful executions |
| Python compile check | Passed | Source/scripts/test syntax is valid in the test interpreter |
| Native Qt UI exercised offscreen | Passed | Window construction; streamed simulated reply; completion controls; memory/settings save; all seven pages; literal text handling |
| Real British George synthesis → local Whisper, run 1 | Passed | 24 kHz audio, 4.693 seconds, peak 0.3784; test sentence recognized correctly |
| Real British George synthesis → local Whisper, run 2 | Passed | 24 kHz audio, 4.693 seconds, peak 0.3754; test sentence recognized correctly |
| Dependency advisory scan | No known vulnerabilities reported in the final pinned set | Package advisory database check at scan time; not an audit of all native DLLs/models or future releases |
| Windows x64 Python 3.11 native wheels | Downloaded; cross-platform resolution dry run passed | Published binary availability and dependency resolution; not execution on Windows |
| Windows x64 Python 3.12 native wheels | Downloaded; cross-platform resolution dry run passed | Same limitation; host-side environment-marker handling is not a complete Windows clean install |

The final repeated-run logs are `test-results/final-run-1.txt` through
`final-run-3.txt`. The summaries, dependency scan and wheel hashes are beside them.
UI screenshots are in `test-results/ui`; generated voice samples/results are in
`test-results/voice`. These fixtures contain scripted test data, not the owner's
real mail, documents, microphone recordings or account tokens.

## Behaviors exercised

- File creation/readback, original-content backups, restoration, stale version
  rejection, competing writes, exact patches including Windows CRLF preservation.
- Real DOCX/XLSX/PPTX/PDF output creation and extraction; corrupt/binary documents
  and suspicious OOXML expansion rejection; parser process operation.
- Workspace boundaries, traversal and symlink escape rejection, protected settings
  paths, exact action/ticket binding, expiry, replay and default-denied approvals.
- Real approved subprocess execution, timeout termination on this OS, cancellation
  before file mutation, bounded search and range reads.
- Source roles, owner corrections, vector similarity, embedding-version separation,
  excluded memories, interrupted job states, durable reminders and quiet hours.
- Model-led tasks with scripted tool calls, actual output receipts, denial, empty
  replies, model failure/recovery, concurrency and step-budget handling.
- Live local HTTP streaming using a simulated Ollama server and a check that remote
  model metadata blocks disclosure before the private prompt is sent.
- Google/Microsoft boundary tests with mocked provider objects, large protected-cache
  chunking, credential rotation/disconnect/incomplete-state checks, unsent draft
  behavior, mail header validation and calendar timezone/order validation.
- Real TLS sockets/certificates, fingerprint mismatch, one-time invitation pairing,
  authenticated requests, revocation, resumable transfer offsets, checksum mismatch,
  traversal filenames and idempotent completed file transfer results.
- Remote task proposals remain proposals and do not execute on arrival.
- Local ComfyUI adapter tested against an HTTP fixture with JSON prompt substitution
  and output import. The fixture is **not** a real diffusion-generation test.
- Private-read taint triggers an outbound request preview; making additional tools
  visible does not grant sensitive-action authority.

## Failures found and corrected during development

- SQLite memory insertion had an incorrect parameter count; memory tests exposed it.
- Quiet-hour alerts originally depended on an in-memory queue; they now persist
  delivery state across scheduler restarts.
- A Qt callback name conflicted with QWidget event dispatch; it was corrected
  before the UI smoke run.
- The selected Kokoro export requires a floating-point speed tensor while the
  voice library supplied an integer for that export variant. The adapter now
  normalizes input tensors to the graph's declared types. A regression test and
  real synthesis checks cover that correction.
- A current PyAV release removed a keyword used by the selected Whisper version.
  PyAV is pinned to a compatible published Windows-wheel version; real transcription
  was rerun after the change.
- Windows credential blobs cannot safely hold a large MSAL cache as one entry.
  Credential Manager storage now chunks caches and atomically publishes a generation.
- The first dependency set had published advisories. Affected libraries and the
  compatible MSAL version were updated, pinned, retested and rescanned.
- UTF-8 metadata reads, Windows handle argument types and CRLF source preservation
  were corrected during platform-oriented review.

## Not established here

Actual Windows 11 clean install, Python launcher/winget/PowerShell/ACL behavior;
Windows Credential Manager operation; speaker/microphone quality and hot-plug;
wake-word reliability and latency; foreground capture/lock/privacy behavior;
real Qwen model intelligence, reasoning quality, long tool sessions and GPU memory;
real Google/UCF authorization/refresh/revocation/consent; notification delivery;
internet/NAT/VPN/firewall pairing across physical computers; actual diffusion/video
generation; native self-update activation/rollback; signed distribution; comprehensive
privacy/security audit or malicious-code sandboxing.

Phone/SIP/PSTN calling, dedicated messaging providers, automatic cross-device memory
sync and unattended distributed workers are not implemented in this preview. See
FEATURE_STATUS.md. Run the provided native checks and manual checklist on each PC
before relying on the application for important work.
