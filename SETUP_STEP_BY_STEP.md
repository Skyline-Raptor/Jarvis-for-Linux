# Jarvis Fresh — Linux Mint setup, step by step

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

Version **1.0.1-preview.1-linux**. This guide replaces the Windows setup guide.
The existing preview's feature limits still apply; see FEATURE_STATUS.md.

## 1. Prepare Linux Mint

1. Use a **64-bit Intel/AMD Linux Mint** installation. Mint 22.x with Cinnamon
   is the primary target. On Mint 21.x the installer downloads an isolated Python
   3.12 runtime; that compatibility path has not been validated on Mint 21 itself.
   ARM computers and LMDE are outside this release's validation.
2. For screen awareness and desktop automation, log out, choose **Cinnamon** or
   **Cinnamon (X11)** in the login screen's session selector, and sign back in.
   Avoid a Wayland session for those two features. Check in a terminal:

   ```bash
   echo "$XDG_SESSION_TYPE"
   ```

   It should say `x11`. You can still use the core UI/chat/files on Wayland.
3. Open Mint's **Driver Manager** and use the NVIDIA driver it recommends for your
   graphics card, if necessary. Reboot after a driver change. In a terminal,
   `nvidia-smi` should show your NVIDIA GPU when its proprietary driver is active.
   Jarvis can run on CPU, with slower AI inference. Do not install CUDA toolkits
   just to start the basic app; optional ComfyUI has its own PyTorch requirements.
4. Keep sufficient free disk space. Your planned 250 GB is ample for the initial
   app and baseline models; optional image/video weights and outputs can grow.
   This is a planning budget, not an enforced quota. Use a local Linux filesystem
   in your home folder; avoid a shared Windows/NTFS partition for the live app,
   Python environments and database.
5. Download the Linux ZIP, right-click it and choose **Extract Here**. Move the
   extracted `Jarvis_Fresh_1.0.1_Linux_Mint` folder to a permanent place, for example
   `~/Applications/Jarvis_Fresh_1.0.1_Linux_Mint`. Do not run inside the ZIP.
6. Open that extracted folder in Mint's file manager, right-click empty space,
   and choose **Open in Terminal**. All following commands assume this terminal
   is in the extracted project folder. You do not need to activate Python manually.

## 2. Install Jarvis and voice

Run:

```bash
bash install.sh
```

1. Run it as your **normal desktop user**, without `sudo` in front. It asks for
   your sudo password only to install Ubuntu/Mint system packages through apt.
   While entering the password, the terminal normally shows no characters.
2. Leave the terminal open. The installer installs Qt/X11/audio/clipboard/FFmpeg
   dependencies, creates private bootstrap and app Python environments, installs
   pinned Linux Python packages, runs the regression suite, and creates a Mint menu entry.
3. It downloads Kokoro's George voice assets and the `small.en` Whisper model.
   Downloads total hundreds of MB and can take several minutes. No paid AI API
   key is needed. These weights are not bundled inside this ZIP.
4. Wait for **Jarvis installed**. If any step fails, read the actual error and the
   `install-logs/` log before proceeding. You can rerun the installer. Python
   packages stay inside the app's environments; distro Python is not replaced.
5. For an initial text-only installation instead, use:

   ```bash
   bash install.sh --skip-voice
   ```

   Later install voice with `bash install_voice.sh`. If voice downloading alone
   fails, the core app/menu is already installed; leave voice/wake off, test chat,
   and rerun `bash install_voice.sh` when the connection works.
6. If apt was deliberately prepared separately, `--skip-system` skips apt; all
   system libraries are still required. It is a troubleshooting/developer option.
7. Keep the install folder in place. To move it later, copy the source to the new
   location, remove the copied `.venv` and `.bootstrap` folders there, and rerun
   installation. Re-enable startup in the relocated app to update its path.

An optional `wheelhouse/` targets CPython **3.12** on Linux **x86_64**. Without it,
the GitHub installer fetches pinned Python packages from PyPI. It also needs apt repositories,
and on systems without Python 3.12, Astral's managed Python download. It is not a
fully offline operating-system/runtime/model installer. `requirements-linux.lock`
pins the full runtime set; `resolved-environment.txt` records what actually installed.

## 3. Install Ollama and local AI models

1. Use the [official Ollama Linux guide](https://docs.ollama.com/linux). One way
   to download and run the official installer is:

   ```bash
   curl -fL https://ollama.com/install.sh -o /tmp/jarvis-ollama-install.sh
   less /tmp/jarvis-ollama-install.sh
   sh /tmp/jarvis-ollama-install.sh
   ```

   Press `q` to leave `less`. The publisher's installer requests sudo and creates
   its system service. This external installer is not bundled or version-pinned.
   If Ollama is already installed and working, keep your existing installation.
2. For the standard system-service installation, keep inference local and disable
   cloud features using a dedicated service override:

   ```bash
   sudo mkdir -p /etc/systemd/system/ollama.service.d
   printf '[Service]\nEnvironment="OLLAMA_NO_CLOUD=1"\nEnvironment="OLLAMA_HOST=127.0.0.1:11434"\n' | sudo tee /etc/systemd/system/ollama.service.d/jarvis-local.conf
   sudo systemctl daemon-reload
   sudo systemctl restart ollama
   systemctl --no-pager status ollama
   ```

   If you intentionally run Ollama manually instead of as a system service, use
   `OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve` in a separate terminal.
   Use one server, not both. Jarvis also rejects remote/cloud model metadata.
3. In the Jarvis project terminal, run:

   ```bash
   bash install_models.sh
   ```

   It pulls `qwen3:8b` for chat/tools, `qwen2.5vl:3b` for vision, and
   `nomic-embed-text` for memory search. Rerun to resume an interrupted pull.
4. Check them with `ollama list`. For lower memory usage you can also run
   `ollama pull qwen3:4b`, then set **model** to `qwen3:4b` inside Jarvis Settings.
   These baseline choices are retained from your existing preview. Actual
   performance depends on VRAM/RAM, drivers and other running applications.
5. Keep Ollama on localhost. Paired Jarvis devices use a separate service; you do
   not need to expose Ollama's port 11434 to your network or the internet.

## 4. Launch and test ordinary chat/files

```bash
bash start_jarvis.sh
```

1. You can also launch **Jarvis Fresh** from Mint's application menu. Opening the
   launcher again brings an existing instance forward instead of starting another.
2. Use **Settings → Check system** to inspect models, voice asset flags and the
   desktop session. A healthy UI without Ollama installed cannot answer with AI yet.
3. Ask a short question. Text should stream into Conversation. Use **Stop** to
   cancel a running request. Models may take longer during their first load.
4. Use **Files → Import files** with a harmless text/document/source file, or
   drag one onto the window. Imported files are copies. Ask Jarvis to read it and
   create a revised copy in the workspace. Inspect the actual output through
   **Open workspace** and check the receipt in **Activity**.
5. For an existing project, use **Authorize folder** for that specific folder,
   then request a change and its relevant tests. Folder access is not an OS sandbox.
6. Review the exact command/action and Details in approval dialogs. Commands run
   with your Linux user permissions. File writes use hashes, backups and atomic
   replacement; **Restore file receipt** refuses to overwrite a subsequently
   changed output. Complex Office formatting/macros/charts are not universally
   preserved, and spreadsheet formulas are not recalculated by this preview.
7. Save a preference in **Memory**, restart Jarvis and confirm it is present.
   This is local stored memory, not model-weight training or automatic knowledge
   sharing with your other computers.

## 5. Enable George voice and check your sound devices

1. Open Mint **Sound** settings. Select your intended input microphone and output
   speakers/headphones and test ordinary desktop recording/playback first.
2. In Jarvis, click **Microphone · listen**, speak a short request and pause.
   Review the recognized text before sending. Capture requests mono 16 kHz input;
   an incompatible endpoint should produce a visible error. USB/Bluetooth device
   switching, driver latency and live audio still need your hardware check.
3. Enable **Speak · British George**, send a short question and listen. The exact
   voice is Kokoro `bm_george`, with 24 kHz generated speech.
4. Optionally enable **Wake microphone**. Say “Jarvis” and the request in the same
   utterance. This uses local chunk transcription, consumes CPU and is not an
   instantaneous dedicated wake detector or speaker-identity authentication.
5. Use **Stop** and the tray's microphone mute when needed. To test generated
   speech/transcription without recording your microphone:

   ```bash
   .venv/bin/python scripts/voice_smoke.py
   ```

6. Once models and voice assets are installed, run `bash native_check.sh` for a
   local model reply and generated-voice report. It does not validate live input,
   speakers, account consent, screen lock or GPU media. Results go in `test-results/`.

## 6. Secure credentials, background operation and screen awareness

1. Linux credentials use the desktop **Secret Service**, normally GNOME Keyring
   on Mint. Sign in normally so your login keyring unlocks. If using automatic
   login or after changing your login password, the keyring may need a separate
   unlock in Mint's **Passwords and Keys** application (install `seahorse` if needed).
2. Jarvis connects to secure services in the background so a locked/missing
   keyring cannot prevent the main window from opening. If Accounts reports a
   problem, unlock your login keyring and click **Connect / retry secure account
   and device services**. If a newly installed keyring has no session service,
   log out and back in first. No plaintext fallback credential file is used.
3. Screen awareness and desktop control require **X11**, a working session D-Bus,
   and a supported Cinnamon/GNOME/XFCE/freedesktop screensaver `GetActive` response.
   If lock state cannot be verified they stop rather than capturing anyway.
   Wayland users should leave those features off or switch to Cinnamon/X11.
4. Turn on **Screen awareness** and focus a harmless test window. Observation
   samples the foreground window, compares changes and asks local vision for a
   short suggestion. It yields to tasks and is not frame-by-frame continuous vision.
5. Add sensitive title fragments in Settings. Test a window titled with one of
   those fragments, then pause observation, then lock your screen. The app should
   stop observation while excluded, paused or locked. Frames remain temporary,
   but exclusions are best effort; pause before handling sensitive content.
6. **Settings → Enable startup** creates a per-user entry in
   `~/.config/autostart/jarvis-fresh.desktop` (or XDG_CONFIG_HOME). It starts in
   the tray at the next graphical login. Disable startup from Settings if unwanted.
7. Closing the window keeps background work running. Reopen it from the tray,
   Mint menu or `bash start_jarvis.sh`. Use **Quit Jarvis** in the sidebar or
   tray **Quit** to stop everything. Sleeping/shutting down the computer pauses work.
8. Test reminders with explicit dates/times and check quiet hours. Scheduled task
   approvals remain action-bound; a job cannot grant itself permission to send,
   execute commands or control the desktop. Missed old jobs can require review.

## 7. Connect personal Gmail and Google Calendar

Provider dashboards and school policy can change; follow their current official instructions if labels differ.

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
8. Each machine signs in separately. The Linux login keyring protects the token
   cache. Revoked/expired sessions require reconnection; tenant policy may require
   periodic MFA even when refresh is otherwise supported.

## 9. Local image generation, editing and video/media

1. Run `bash install_media.sh` for FFmpeg. Close/reopen Jarvis after installation so
   the updated PATH is visible. FFmpeg runs only after approving the exact command.
2. Install the free **local ComfyUI** from its [official repository](https://github.com/Comfy-Org/ComfyUI#installing).
   Use its Linux manual installation instructions in a separate environment, and
   follow its model instructions and keep its listener at `127.0.0.1:8188`.
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

## 10. Pair another computer

1. Install and test Jarvis independently on each computer. Models, memories and
   account authorizations are separate; tokens are not imported from Windows.
2. Use an existing private VPN or install Tailscale following its
   [Linux guide](https://tailscale.com/download/linux) on Mint. Each computer must
   be awake, connected to the private network and running Jarvis.
3. Unlock the login keyring. In **Devices**, start the receiver on the destination.
   It listens on TCP 7443. Receiver startup is manual after every Jarvis restart.
4. If Mint's UFW firewall is enabled, allow only the other device's VPN address.
   For example, replace `100.101.102.103` with the actual other machine's address:

   ```bash
   sudo ufw allow in on tailscale0 from 100.101.102.103 to any port 7443 proto tcp
   ```

   If using another VPN, use its interface and address. Do not forward this port
   on the public router and do not open port 11434 for pairing.
5. On the receiver create a five-minute invitation. Copy the complete certificate
   fingerprint and single-use invitation directly to the sending device's Devices
   form, along with the receiver's VPN address. Keep invitations out of model chat.
6. Pair, verify a small test file transfer and inspect the received inbox. Use
   **Accept received file** to import a `.received` file into the workspace.
   Transfers are pinned TLS, hash-checked and limited to 128 MiB per file.
7. Pair in reverse for sending both ways. A remote task stays a proposal until
   the receiver reviews and sends it locally. Automatic conversations/memory sync,
   unattended remote execution and distributed scheduling are not implemented.
8. Revoke unused devices from Devices. Changing/loss of the local keyring can
   require re-pairing. The protocol is retained, but this Linux build has not been
   tested against a live Windows installation or across an actual VPN here.

## 11. Data, backups and reviewed source updates

- Default live data: `~/.local/share/jarvis-fresh/` (or
  `$XDG_DATA_HOME/jarvis-fresh`). It contains settings, SQLite history/memory,
  workspace files, voice assets, device certificates and logs. The directory is
  private to your user. `JARVIS_HOME` can override it; keep that value consistent
  for terminal, menu and startup launches if customized.
- Ollama and Hugging Face keep separate caches. Ollama installed as a system
  service often uses its service user's model directory, not your interactive
  user's cache. Inspect its service configuration before moving large model files.
- Quit Jarvis before copying the data directory for backup. Copy the source folder
  separately if you want your own modified app. Do not share your data backup.
  Account/device secrets also live in the OS keyring: copying app data alone is
  not a complete credential backup. On a new installation, reconnect/re-pair.
- Chats/files are not encrypted at rest by the application. Use your chosen disk
  encryption and system backup protections. Do not delete a keyring to fix login.
- Core improvement creates a separate candidate copy; it does not silently modify
  the running source. Quit Jarvis, then run `bash apply_candidate.sh /full/path/to/candidate`.
  Review the candidate first. The helper requires `TEST`, runs candidate tests
  with your current user permissions, then requires `APPLY`, creates a source ZIP
  under `CoreBackups`, and replaces only `jarvis`, `tests`, `scripts`. Dependencies,
  root launchers and data are not updated by this source-only helper.
- On an ordinary copy failure the helper restores the prior source. Power loss
  during replacement can still require manual restore. To roll back, quit Jarvis,
  remove the installed `jarvis`, `tests`, `scripts` folders, then extract the
  backup ZIP into the install folder. Rerun the test script before starting.
- To remove the app, disable startup, quit Jarvis, remove the menu entry
  `~/.local/share/applications/jarvis-fresh.desktop`, and remove the install folder.
  Preserve the separate data directory unless you deliberately want to erase it.
  Ollama/models and connected-account authorizations are managed separately.

## 12. Run checks and troubleshoot

```bash
bash test_jarvis.sh
bash native_check.sh
```

The first runs regression tests and offscreen UI simulation. The second requires
installed Ollama models and voice assets. Neither establishes zero bugs. The
included report separates real operations, mocked boundaries and unverified hardware.

| Symptom | Next step |
|---|---|
| apt dependency/download failed | Check Mint's network/repositories and install log; rerun installer after resolving it. |
| Python 3.12 download failed on Mint 21 | Restore network access to Astral/GitHub, or use a separately installed Python 3.12; rerun. Do not replace `/usr/bin/python3`. |
| Qt xcb plugin cannot load | Rerun system package installation; use `QT_DEBUG_PLUGINS=1 bash start_jarvis.sh` and inspect the runtime log. |
| Menu launch does nothing | Run `bash start_jarvis.sh` from a terminal; read `~/.local/share/jarvis-fresh/runtime.log`; confirm the folder was not moved. |
| Connection refused / missing model | Check `systemctl status ollama`, `ollama list` and Jarvis model settings. |
| Slow / out of memory | Close ComfyUI/games; use qwen3:4b; pause screen awareness; check `nvidia-smi` and `ollama ps`. |
| Keyring unavailable / locked | Unlock Passwords and Keys, log out/in if needed, then click Accounts → Connect / retry. Text/files can still work. |
| Screen says X11 required | Choose Cinnamon/X11 at login. This port does not support Wayland screen capture/control. |
| Cannot verify screen lock | Confirm the Cinnamon screensaver and session D-Bus are running; do not disable the privacy check. |
| No microphone / PortAudio error | Check Mint Sound input/default device and libportaudio2; test without wake mode first. |
| No George voice | Run `bash install_voice.sh`, then the generated-audio smoke test. |
| Folder access denied | Authorize the specific project folder in Files; core/settings/credentials stay protected. |
| Google invalid_grant | Reconnect and check token expiry/provider authorization. |
| UCF admin consent blocked | Check tenant/app registration with UCF IT. |
| Pairing failed | Check private VPN reachability, receiver running, TCP 7443 rule, exact fingerprint and unexpired invitation. |
| ComfyUI job failed | Run that API workflow directly in ComfyUI; check model filenames and installed nodes. |

For developer-only isolated native checks on a machine that permits X11/D-Bus
sockets: install `xvfb openbox gnome-keyring`, install
`tests/requirements-native.txt` into the app environment, and run
`.venv/bin/python scripts/linux_native_smoke.py`. This creates a temporary HOME,
virtual X server, test screensaver service and temporary keyring; it is separate
from regression tests. It was blocked by desktop socket restrictions in the build
environment, so its inclusion is not a claim that it passed.

Official references: [Qt Linux libraries](https://doc.qt.io/qt-6/linux-requirements.html),
[uv Python management](https://docs.astral.sh/uv/guides/install-python/),
[Python keyring](https://keyring.readthedocs.io/en/latest/),
[Ollama Linux](https://docs.ollama.com/linux),
[ComfyUI manual installation](https://docs.comfy.org/installation/manual_install).
