# Feature status — 1.0.0-preview.1

This release is a new runnable Python/Qt application with setup scripts and tests.
It is an engineering preview, not a complete or certified implementation of every
item in the broader design specification. The old source packages were reference
material; their complete runtimes and historical test counts are not part of this build.

| Area | Implemented behavior | Verification / remaining boundary |
|---|---|---|
| Desktop UI | Native Qt chat, Files, Activity, Memory, Accounts, Devices, Settings; drag/drop; tray/startup controls | Offscreen navigation/chat/settings exercised on Linux; native Windows tray, DPI, dialogs/startup unverified |
| Local AI | Ollama streaming, tool calls, local-only metadata checks, cancellation, fast/deeper Qwen3 option | HTTP transport exercised with a simulated server; real Qwen reasoning/tool quality and GPU performance unverified |
| Files | Imports, explicit roots, name search, text/code read/write/patch, source hashes, atomic writes, backups and rollback | Real filesystem conflict/recovery tests; no claim of OS-atomic compare-and-swap against a hostile process changing junctions/paths |
| Documents | DOCX/XLSX/PPTX/PDF extraction and basic structured creation; bounded parser subprocesses | Round-trip tests passed; complex formatting/macros/charts/comments/recalculation/general binary editing not universal |
| Coding | Source generation, exact patches, approved argv execution, bounded output/timeouts, process-tree termination attempts | Real code/test subprocesses exercised on Linux; Windows termination still native check; no hostile-code security sandbox |
| Memory | SQLite history, explicit owner corrections, active/reference/excluded roles, lexical/local semantic search and bounded indexing | Real store tests; semantic arithmetic tested with vectors, real embedding model quality unverified; no automatic model retraining |
| Judgment/personality | Seven requested traits in default instructions; task steps, receipts and permission separation | Behavioral design is implemented; stronger emotional intelligence/creativity/common-sense competence is not established by scripted tests |
| Web | Public retrieval with address pinning, size/redirect bounds; DDGS search; public browser opening | Address/security cases tested; live search coverage and site blocking vary; no full DOM browser agent in this release |
| Permissions | Single-use, expiring action-bound approvals; protected core/credential paths; task roots; outgoing preview after private reads | Regression tests pass; source-text prompt injection can still influence model reasoning and low-risk permitted work; no claim of perfect injection resistance or DLP |
| Voice | Exact bm_george identity, local Kokoro, local Whisper, one-utterance button, chunk-based wake activation, worker deadlines and Stop | Two real generated-speech/transcription runs passed; live microphone/playback/hotplug/latency/wake accuracy unverified; no global keyboard PTT |
| Screen | Adaptive foreground screenshot/vision suggestions, exclusions, lock check, pause, task/GPU yielding | Implementation present; Windows capture/lock/privacy exclusions and visual suggestion quality require native testing; not continuous frame-by-frame understanding |
| Accounts | Separate Google and Microsoft OAuth; read mail/calendar, unsent drafts, approved send/event creation; Windows-protected chunked credentials | Mock/provider-boundary tests and imports passed; no live account sessions tested; school administrator policy may block consent |
| Background work | Durable reminders, quiet hours, deduplicated alerts, 5-minute account polling, approved scheduled tasks and reviewed restart states | Reminder/restart tests; real notifications/account sync and sleep/wake behavior unverified |
| Device connections | Explicit pairing, pinned TLS, per-device credentials/revocation, resumable hash-checked inbox transfers, reviewed remote task proposals | Real TLS/socket tests on one host; internet/VPN/firewall cases unverified; receiver starts manually; 128 MiB/file; no arbitrary remote browsing/execution |
| Media | Local ComfyUI image/edit/video workflow adapter, sample image and SVD workflows, output import; FFmpeg conversion; audio transcription; sampled video vision | Adapter simulations and voice pipeline tested; actual diffusion/video models and GPU workflows unverified; external setup required |
| Improvement | Owner corrections, procedure memory, staged project/core copies, approved tests, manual activation and backup script | Core staging behavior implemented; native activation/rollback script unverified; not autonomous weight training or silent self-patching |
| Communications beyond email | Desktop tools can help operate separately installed applications with approval | Dedicated messaging providers, autonomous SIP/PSTN calls and old VB-CABLE/Linphone call audio are **not implemented** |
| Cross-device memory | Chosen files can be transferred to another paired installation | Automatic conversation/memory/settings synchronization, distributed worker scheduling and unattended remote execution are **not implemented** |
| Encryption/recovery | OAuth/device secrets in Windows Credential Manager; encrypted private key; TLS transport; user-profile file ACL setup | Chat/memory/documents are not application-level encrypted; use Windows protections/BitLocker as needed. No encrypted vault export or signed updates |
| Portability | Per-user Python setup for Windows 11 x64 with CPU/smaller-model options | Windows clean install has not been run here. ARM64 native support, all hardware combinations and packaged signed EXE remain unverified/unprovided |

The installer obtains dependencies/models from external publishers. Core AI does
not need paid API keys. Google/Microsoft require application registration and
authorization; sessions can expire. Public search, model hosts and optional VPN
services do not have an unconditional permanent free/unlimited availability guarantee.

Security conventions retained from the source review: reasoning does not grant
authority; current and historical evidence stay distinguishable; commands and
outputs have receipts; drafts remain unsent; document contents are untrusted;
credentials are not supplied to the model; approvals are bound to exact payloads.
The implementation is not a transplant or a full audit of either old product.
