# Jarvis Fresh — step-by-step Windows setup

Version 1.0.0-preview.1. This guide belongs to the runnable engineering preview.
Read FEATURE_STATUS.md for the precise capability boundary. There is no claim
that this release duplicates ChatGPT's model or has zero bugs.

## 1. Prepare the laptop first

1. Use Windows 11 **x64**, with your normal Windows user account. This package
   has not been validated for native Windows ARM64. Your RTX 4060 laptop and
   i7-10700F/RTX 2060 desktop are the intended hardware class.
2. Plug in the laptop and use a performance power mode while testing.
3. Update the NVIDIA driver through NVIDIA's official installer/app if needed.
4. Keep about 250 GB free on the SSD you intend to use. The initial chat/voice
   setup uses substantially less; image/video packs and outputs can grow quickly.
   Ollama and Hugging Face have their own model caches in your user profile.
   The 250 GB target is a planning allowance, not a total system-wide disk quota.
5. Download this ZIP, right-click it and choose **Extract All**. Choose a permanent
   location such as `C:\JarvisFresh`. Do not run scripts from inside the ZIP.
   Avoid OneDrive/network folders for the application and live database.
6. If Windows shows a downloaded-file checkbox in the ZIP's Properties, use
   **Unblock** before extracting if available. Review the source before running
   an unsigned script; this package is not a code-signed installer.

## 2. Install the application and voice

1. Open the extracted folder. Double-click **Install_Jarvis.cmd**.
2. It finds Python 3.11/3.12, or uses Windows Package Manager to install Python
   3.11. If `winget` is unavailable, install Python 3.11 x64 from
   [python.org](https://www.python.org/downloads/windows/), with the launcher,
   then rerun Install_Jarvis.cmd. Microsoft Visual C++ 2015–2022 x64 runtime may
   also be required by native inference libraries; use Microsoft's official installer.
3. Let the window stay open. It creates a private Python environment, downloads
   dependencies from the included Windows wheelhouse, runs the core tests, secures the data folder, and installs
   Kokoro British George plus the local `small.en` speech model. Large downloads
   may show little progress while a file is being fetched.
4. Wait for the explicit **Jarvis installed** message. A failed step must be
   resolved before treating that capability as ready. `install.log` is in the
   extracted folder. If only voice download fails, you can rerun
   **Install_Voice.cmd**; core chat can be used with voice unchecked.
5. Do not rename or move the application folder after installation. To relocate
   it, copy the source to the new location, remove its copied `.venv`, and rerun
   installation there. Your separate user-data folder stays in place.

The installer uses free packages and local models. The ZIP includes Python dependency
packages for Windows x64/Python 3.11 and 3.12, so those packages can be installed
without a fresh dependency download. It does not bundle a Windows Python runtime,
Ollama or all model weights. The voice installer records asset
URLs and hashes; those hashes are download receipts, not independently verified
publisher signatures. A constraints snapshot pins the dependency set; `resolved-environment.txt`
records what was actually installed, including transitive dependencies.

## 3. Install the local AI models

1. Install [Ollama for Windows](https://ollama.com/download/windows). Open it;
   it normally stays in the system tray. No Ollama sign-in is needed for these
   downloaded local models.
2. Close and reopen the folder/terminal if a newly installed `ollama` command
   cannot be found.
3. Double-click **Install_Models.cmd**.
4. Choose **1** for the balanced RTX 2060/4060 profile. It downloads `qwen3:8b`,
   `qwen2.5vl:3b` for vision, and `nomic-embed-text` for memory search.
   Choose **2** for a smaller `qwen3:4b` conversation model on lower-memory PCs.
   CPU operation is possible but slower, and weak models may struggle with tools.
5. If a download fails, rerun the script. Ollama can resume its own downloads.
6. After completion, **quit Ollama from its tray menu and reopen it**. The setup
   sets the user-level `OLLAMA_NO_CLOUD=1` environment variable. Restarting applies
   it to the server. Jarvis also checks model metadata and rejects remote models
   before sending conversation content.
7. Keep Ollama bound to its default localhost interface. Do not expose port 11434
   to your network. The device service is separate and does not need that port.

These are configurable baseline models, not a benchmark claim that they are the
strongest choices for your exact hardware. Change names in Settings after pulling
another **local, tool-capable** model. New model families may have different
thinking/tool conventions and must be checked before everyday use.

## 4. Start Jarvis and check the basics

1. Double-click **Start_Jarvis.cmd**.
2. Open **Settings → Check system**. Check that your conversation, vision and
   embedding models appear under installed models, and both voice asset flags
   are true if you installed voice.
3. Open **Files → Import files**, or drag a harmless `.txt`, `.docx`, `.xlsx`,
   `.pptx`, `.pdf`, image, or source file onto the window. Imports are copies;
   they do not replace the original selected file.
4. In Conversation, add: “Read this file and create a revised copy in my workspace.
   Keep the meaning and tell me what changed.” Click **Send** or **Ctrl+Enter**.
5. Use **Files → Open workspace** to inspect the result. Use **Activity → Refresh**
   to inspect receipts and errors. A model's sentence claiming success is not proof;
   look for a file/command receipt and inspect the actual output.
6. For an existing code project, use **Files → Authorize folder** and choose that
   project directory. Say what to fix and ask it to run relevant tests. You can
   remove that folder's access later. Authorizing a folder gives task-related
   file access inside it; it is not an operating-system sandbox.
7. When a command, sending action, desktop operation, calendar write, scheduled
   task, or device disclosure needs approval, review the exact payload in the
   dialog and its **Details**. Approval expires and applies once to that action.
   Commands run with your Windows account rights; there is no hostile-code VM.
8. If stopped or interrupted, completed file actions remain in Activity. Use
   **Continue selected task** to load a continuation into chat, then review/send.
   This resumes from recorded information; it does not restore an arbitrary
   process's RAM state or guarantee that a model will avoid every duplicate step.

File changes use hashes, backups and atomic replacement. Activity receipts identify
the backup; **Restore file receipt** restores it only if the output has not since
changed. Office creation is structured content generation, not a promise to preserve
all formatting, macros, charts, formulas or comments in an existing complex file.
Word/PowerPoint output is basic; Excel formulas are preserved as source formulas
but are not recalculated by Jarvis. Unsupported/encrypted formats need conversion
or an explicitly approved custom program. No Office macros are executed by readers.

## 5. Set up British George and the microphone

1. In **Windows Settings → System → Sound**, choose your normal microphone and
   speakers/headphones as the default devices. Keep VB-CABLE and telephony devices
   out of this initial ordinary-voice check.
2. In **Privacy & security → Microphone**, allow desktop applications to use the mic.
3. In Jarvis, click **Microphone · listen**, speak a short request, then pause.
   This records one utterance, stops after silence, and puts the recognized words
   in the input box for you to review and Send. It is button-activated listening;
   there is no global keyboard push-to-talk hotkey in this preview.
4. Turn on **Speak · British George**, send a short text question, and check playback.
   Text streams first; speech follows the completed answer.
5. Turn on **Wake microphone** to use “Jarvis, …your request…”. Speak the wake word
   and request in the same utterance. This implementation transcribes short local
   chunks, so activation takes seconds and consumes CPU. It is not an instantaneous
   dedicated wake-word detector or voice identity verification.
6. Use **Stop** to interrupt a task/audio. Use the tray menu to mute wake listening.
   Microphone silence, device errors and worker timeouts should produce a visible
   status instead of freezing the window.
7. Run **Native_Check.cmd** to check actual local model/voice operation and create
   a diagnostic report on your machine. The included test voice files were synthesized
   and transcribed here, but your microphone, speakers, drivers, latency and accent
   recognition still require this native check.

If speech is static or distorted, test normal speakers first and check Windows
default endpoints. This release does **not** reuse the old automatic call-audio
route. British George uses `bm_george`, Kokoro ONNX and 24 kHz generated audio.

## 6. Background operation, memory and screen help

1. Turn on **Screen awareness** when ready. Jarvis samples the foreground window
   about every 30 seconds, runs local vision when the screen changes, and offers
   a brief suggestion for a clear problem. Suggestions are rate limited to about
   once per three minutes and yield to active tasks.
2. Add sensitive app/window title fragments in Settings. Pause observation before
   handling sensitive content. Exclusions are **best effort**, based on foreground
   title and desktop availability; they are not perfect secret detection. The
   whole foreground window can contain other people's private information.
3. Raw observation frames are processed temporarily in memory and are not archived
   or automatically saved as long-term memory. Suggestions are notifications.
   Observing something does not grant permission to operate on it.
4. Use **Memory** to save owner corrections/preferences and delete records. Ask to
   “index this authorized project folder as reference material” for bounded content
   indexing and semantic retrieval. Historical material stays reference context
   and does not automatically become an overdue obligation.
5. In **Settings**, save quiet hours, then click **Enable startup** if desired.
   Closing the window keeps Jarvis running in the tray when a tray is available.
   **Quit** stops background services. Laptop sleep/hibernation pauses all work.
6. Ask for a reminder with a clear date/time. Ask for a scheduled task only when
   you want work performed later; inspect the scheduled action approval. Recurrence
   must be at least five minutes. Consequential tools still need a local approval
   at execution; unattended approval requests expire. Missed scheduled tasks older
   than 24 hours are held for review.

## 7. Connect personal Gmail and Google Calendar

1. Visit [Google Cloud Console](https://console.cloud.google.com/) using your
   personal account. Create a project for your own Jarvis installation.
2. Enable **Gmail API** and **Google Calendar API** in the project's API Library.
3. Configure the **Google Auth Platform / OAuth consent screen**: enter an app
   name and contact email, choose the appropriate external audience, and add
   your own Gmail address as a test user while in Testing.
4. Create an **OAuth client ID → Desktop app**. Download the client JSON to a
   private local folder. This is an application registration, not a paid AI key.
5. In Jarvis **Accounts → Connect Google**, select that JSON. Complete sign-in in
   your browser. Do not paste your password or tokens into Jarvis chat.
6. The requested scopes allow reading mail, composing/sending drafts, and calendar
   events. Jarvis's broker separately asks before sending and calendar creation.
   If you do not want these scopes, do not connect this preview's combined connector.
7. Test: “Show my next Google Calendar events.” Then “Find my unread Gmail.”
   Test draft creation first: “Draft an email to [your own address], subject Jarvis
   test, saying this is a draft. Do not send.” Verify it is unsent in Gmail Drafts.
8. Google Testing refresh tokens for these scopes normally expire after seven days.
   Reconnect when requested. Changing publication status is a Google process and
   can involve warnings/review; this release cannot promise a never-expiring login.
9. For revocation, use **Disconnect Google** and Google's account permissions page.
   The local disconnect removes stored credentials but does not itself revoke the
   provider's authorization record.

## 8. Connect UCF Outlook and its calendar

1. Open [Microsoft Entra admin center](https://entra.microsoft.com/). An application
   registration for your account/tenant is required. UCF may restrict who can
   register apps or consent. If blocked, ask UCF IT whether a personal local
   desktop app with the delegated permissions below is allowed; do not bypass
   the university's restrictions.
2. Create/register a **public desktop client**. Choose a supported account type
   appropriate for the tenant. Add **Mobile and desktop applications** with the
   loopback redirect URI `http://localhost`.
3. Add delegated Microsoft Graph permissions: **User.Read, Mail.Read, Mail.ReadWrite,
   Mail.Send, Calendars.ReadWrite**. Grant your own consent or obtain required
   administrator approval. Do not create or embed a confidential-client secret.
4. Copy the **Application (client) ID**. In Jarvis Accounts, paste it into Microsoft
   application client ID. Use the authorized **tenant ID** if supplied, otherwise
   `organizations` for your school/work sign-in.
5. Click **Connect Microsoft / UCF**. Sign in in the provider browser and finish MFA.
6. Test: “Show my upcoming Microsoft calendar events.” Then ask for recent Outlook
   mail metadata and an **unsent** test draft to yourself.
7. Once connected, the background service polls about every five minutes for unread
   mail and events in the next 24 hours. It lists calendar events over a two-week
   window on request. Notifications are based on account data; it does not reliably
   infer every assignment deadline from an arbitrary email or access Canvas.
8. Each machine signs in separately. Windows Credential Manager protects the token
   cache. Revoked/expired sessions require reconnection; tenant policy may require
   periodic MFA even when refresh is otherwise supported.

## 9. Local image generation, editing and video/media

1. Run **Install_Media.cmd** for FFmpeg. Close/reopen Jarvis after installation so
   the updated PATH is visible. FFmpeg runs only after approving the exact command.
2. Install the free **local ComfyUI** from its [official repository](https://github.com/Comfy-Org/ComfyUI#installing).
   The Windows portable NVIDIA build is an option for your machines. Follow its
   own installation/model instructions and keep its listener at `127.0.0.1:8188`.
   The hosted Comfy API is not used by this adapter.
3. For the supplied basic image workflows, obtain a compatible Stable Diffusion
   1.5 checkpoint from its authorized publisher and place it in ComfyUI's
   `models/checkpoints` folder as `v1-5-pruned-emaonly.safetensors`, or edit the
   `ckpt_name` in the supplied JSON to match your checkpoint's actual name. Check
   the model's license before using or redistributing it.
4. Generate one image directly in ComfyUI first. This confirms that your GPU,
   PyTorch install, checkpoint and nodes work independently of Jarvis.
5. In Jarvis Settings, put the full path to `docs/txt2img_api.json` in **ComfyUI API
   workflow JSON**. Save. Ask for an image; `{{prompt}}` is replaced by your prompt.
6. For image editing, select `docs/img2img_api.json`, load a source image into the
   workspace and ask to transform it. `{{input}}` is replaced by a locally uploaded
   image filename. This is whole-image diffusion editing, not a precision layer editor.
7. `docs/image_to_video_api.json` is a starting workflow for **Stable Video Diffusion
   image-to-video**, requiring the compatible `svd.safetensors` checkpoint and
   standard SVD nodes. Check the model's current access/license terms. It animates
   an input image into an animated WebP; SVD does not use the text prompt for
   text-controlled motion. Validate in ComfyUI first. This supplied workflow has
   not been GPU-tested here and may exceed practical VRAM/RAM on your systems.
8. For other image/video pipelines, export a working local workflow using
   **File → Export (API)** in ComfyUI. Replace its text/input values with the
   appropriate placeholders and select that file in Jarvis. Trust the workflow
   and installed nodes as local code. Do not add cloud/API nodes; the local-only
   contract does not turn an arbitrary third-party workflow into trusted code.
9. Generated image/video files recognized by the adapter are copied into
   `Workspace/Generated`. Stop detaches a ComfyUI job; it does not silently issue
   a global interrupt against other jobs in a shared ComfyUI instance.
10. For video understanding, Jarvis samples up to six frames with local vision;
    ask for audio transcription separately. It does not inspect every frame.

Image/video quality, speed, supported durations and available styles depend on
the separately installed models. The ComfyUI path is configurable integration,
not a tested universal image/video generator. Close ComfyUI/unload its model when
chat performance suffers; Jarvis's internal queue cannot fully arbitrate GPU memory
against an independently running external application.

## 10. Set up the desktop and encrypted connections

1. Repeat sections 1–5 on the desktop. Each installation has its own models,
   conversations, settings, credentials and independent local operation.
2. Install [Tailscale](https://tailscale.com/download/windows) on both computers
   or use your existing private VPN. Tailscale currently has a free Personal plan;
   its service terms and availability can change. Both machines must be awake,
   online, signed into the private network and running Jarvis.
3. On the **receiving** computer, go to **Devices → Start receiver**. It listens
   on TCP 7443. Keep firewall access limited to your private VPN. Do not forward
   this port publicly. Receiver startup is manual in this preview, including
   after restarting Jarvis.
4. If necessary, an administrator can add a narrow Windows Firewall rule for the
   other machine's exact Tailscale IP. In an elevated PowerShell, replace the IP:

   ```powershell
   New-NetFirewallRule -DisplayName 'Jarvis paired device' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 7443 -RemoteAddress '100.101.102.103' -Profile Any
   ```

5. On the receiver, choose **Create 5-minute invitation**. Copy its full 64-character
   certificate fingerprint and single-use invitation directly between your devices.
   An invitation is a secret. Do not put it into the model's chat/memory.
6. On the **sending** computer, enter the receiver's Tailscale IP/name, fingerprint
   and invitation. Click **Pair to receiver**. If the fingerprint does not match,
   the request fails before the invitation is sent. Never work around a mismatch.
7. Repeat in the reverse direction to send both ways. Both directions use separate
   authentication credentials. Pairing does not give the other device arbitrary
   filesystem access or automatic permission to execute commands.
8. In Conversation, ask to send an authorized file to the displayed peer ID.
   Approve the exact file/device. Files up to 128 MiB are supported per transfer.
   Retry an interrupted transfer to resume from its acknowledged offset. Finished
   transfers are hash checked and duplicate submissions return the same receipt.
9. On the receiver, use **Open received files** to inspect the quarantined inbox,
   then **Accept received file** to copy the selected `.received` item to a normal
   filename in your authorized workspace. Nothing auto-runs on arrival.
10. A proposed remote task stays pending until you choose **Review proposed tasks**
    on the receiving device, load it into chat, review and Send. This is reviewed
    task delegation, not fully unattended distributed execution.
11. Revoke devices in Devices. Re-pair after resetting a device identity. Private
    keys/passwords are not recoverable merely by copying the application folder;
    identity recovery/export is not implemented. Reauthorize after a clean reinstall.

Automatic bidirectional memory/conversation sync is not implemented. You can exchange
chosen files now; do not synchronize a live SQLite database or credential folders.

## 11. Self-improvement, backups and uninstall

1. Correct Jarvis explicitly and save important corrections in Memory. Useful
   successful procedures can be recorded and retrieved; this is not weight retraining.
2. Ask Jarvis to stage an improvement. It copies a project or its own source into
   `Workspace/Candidates`, where edits and approved tests can be performed.
3. Inspect the candidate. Tests themselves are code and run with user rights.
   Passing a test suite does not establish that a proposed self-change is safe.
4. To activate a Jarvis core candidate, **quit Jarvis**, run **Apply_Candidate.cmd**,
   enter the candidate path, type **TEST**, inspect the results, and type **APPLY**
   only when you want the source copied into the installation. This preview's
   activator replaces source files; it does not automatically reconcile dependency
   changes or remove obsolete files. Keep the original release ZIP.
5. A timestamped rollback archive is saved under the data folder's CoreBackups.
   Close Jarvis before extracting a rollback archive over the installation.
6. For a data backup, Quit Jarvis first, then copy `%LOCALAPPDATA%\JarvisFresh`
   to your own encrypted backup destination. The account/token vault is Windows-
   protected separately and should be reauthorized rather than copied to another PC.
   Normal memory/chat/output files are not application-level encrypted; Windows
   profile access controls and optional BitLocker provide the surrounding protection.
7. To uninstall, disable startup, disconnect accounts, stop/revoke peers and Quit.
   Delete the application folder. User data is retained until you deliberately
   remove it. Ollama models, Hugging Face caches and ComfyUI are separate installs.

## 12. Native acceptance checklist and troubleshooting

Run **Test_Jarvis.cmd** on each machine. Run **Native_Check.cmd** for a real local
model and generated-voice check. Then manually verify: imported-file edits/backups;
short and difficult questions; microphone and speaker behavior; wake mute/Stop;
screen exclusion/pause/lock; account draft versus send approval; quiet-hour alerts;
restarting from the tray; and a file transfer with a temporarily disconnected VPN.

The included tests and simulations reduce defects but do not establish zero bugs,
professional security audit coverage, model accuracy, or clean-install success on
every Windows device. The UI was exercised offscreen on Linux; Windows-native
screens, tray, drivers and permissions still need your own checks.

| Symptom | What to do |
|---|---|
| Chat says connection refused | Start Ollama. Check `ollama list`, then Settings → Check system. |
| Model not found | Rerun Install_Models.cmd or select an installed local model. |
| Slow answers/out of memory | Close games/ComfyUI; choose qwen3:4b; pause observation. First model load is slower. |
| Blank UI / DLL load error | Keep the extracted folder intact; reinstall dependencies; install Microsoft VC++ x64 runtime; check runtime.log. |
| No microphone input | Check Windows default input and privacy permission. Test without wake listening and without VB-CABLE first. |
| No George voice | Rerun Install_Voice.cmd; verify both asset flags; use Native_Check.cmd. |
| Search is empty/rate limited | Retry with a simpler public query or ask to open a search site in the browser. Public websites can block automated retrieval. |
| Folder denied | Add its specific project folder through Files. Application/credential paths remain protected. |
| Approval expires unattended | Repeat the task when you can review it. Scheduled jobs cannot grant themselves new authority. |
| Google invalid_grant | Reconnect; check Testing token expiry and revoked access. |
| UCF sign-in/admin consent error | Check tenant/client registration and ask UCF IT about permitted delegated scopes. |
| Peer won't connect | Both awake/online? VPN IP reachable? Receiver started? TCP 7443 allowed from the other VPN IP? Fingerprint exact? |
| Received file not readable | Use Accept received file; quarantine deliberately appends .received. |
| ComfyUI generation error | Test the same API workflow directly in ComfyUI; check checkpoint names and missing nodes. |

Before sharing diagnostics, review them for private paths, mail/file contents and
other personal data. Relevant files are `install.log`, `resolved-environment.txt`,
the release's `test-results` folder, and `%LOCALAPPDATA%\JarvisFresh\runtime.log`.

Primary references checked during implementation:
[Ollama API](https://docs.ollama.com/api),
[Ollama local/cloud settings](https://docs.ollama.com/faq),
[Google desktop Gmail quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python),
[Google OAuth](https://developers.google.com/identity/protocols/oauth2),
[MSAL Python](https://learn.microsoft.com/entra/msal/python/getting-started/acquiring-tokens),
[Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx),
[ComfyUI local API example](https://github.com/Comfy-Org/ComfyUI/blob/master/script_examples/basic_api_example.py),
[ComfyUI image-to-video examples](https://comfyanonymous.github.io/ComfyUI_examples/video/),
[Tailscale plans](https://tailscale.com/pricing).
