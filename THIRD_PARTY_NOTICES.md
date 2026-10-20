GitHub source edition: third-party wheels, model weights and external applications
are installed separately; an optional local wheelhouse retains its publishers' licenses.

# Third-party components

The original downloadable release contains the new application source, scripts, documentation and test
fixtures/results, plus Python dependency wheels for Linux x86_64 / CPython 3.12. Each wheel retains
its own license files and metadata. Model weights and external applications are
obtained separately by their installers and retain their own licenses.

Principal upstream projects include Python (PSF license), uv (MIT/Apache 2.0), SecretStorage, Jeepney, python3-Xlib, Qt/PySide (LGPL/GPL or
commercial terms as supplied by Qt), Ollama (MIT), Kokoro-82M weights (Apache 2.0),
kokoro-onnx, faster-whisper/Whisper, CTranslate2, ONNX Runtime, PyAV, FFmpeg,
cryptography, keyring, python-docx, openpyxl, python-pptx, pypdf, ReportLab, Pillow,
DDGS, MSS, PyAutoGUI, pyperclip, Google API/Auth libraries, Requests and MSAL.
Consult the installed distributions' license files and model cards for exact terms
and transitive components. FFmpeg licenses depend on the selected binary build.

Optional ComfyUI is GPL-licensed; diffusion checkpoints and custom nodes have
their own licenses and usage terms. Tailscale is an optional service with its own
client licenses and service terms; it is not a bundled Jarvis relay service.

The new source is delivered for your use and modification. It does not include
either uploaded legacy runtime or private ChatGPT model/code. Source-review ideas
are documented in the supplied design baseline; integrations do not transfer
ownership of external models, services or third-party code.
