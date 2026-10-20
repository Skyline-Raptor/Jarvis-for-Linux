# GitHub import — Jarvis-for-Linux

Imported 20 October 2026 from `Jarvis_Fresh_1.0.1_Linux_Mint.zip`.
Original archive SHA-256: `180379a1d8664c017001700bc1c92b3137c558d89d25bd380d712a51b5fc5928`.

The application modules, installers, setup documents, tests, example media workflows
and historical validation results are included. Third-party wheel caches, Python
environments, downloaded model weights and runtime user data are excluded from Git.
The GitHub installer downloads the same pinned dependencies when no wheel cache exists;
a supplied complete compatible cache keeps the original offline package mode.

Repository-specific changes:

- Add Git ignore rules, portable line-ending attributes and GitHub quick-start instructions.
- Adapt core/voice installers to select PyPI for a source checkout, or a local cache for offline setup.
- Keep Windows-only launchers under their archived reference directory, away from Linux launch commands.

The manifests under `docs/package-provenance/` describe the original full download,
not this source checkout. The root manifest describes this repository snapshot.
Historical test reports retain their original platform and verification boundaries.
Import validation is recorded below; it does not certify a native Windows or Mint
installation. No additional source license has been assigned by this import.

## Import validation

- Python source compilation passed.
- 125-test regression suite passed in this Linux/CPython 3.12 environment.
- Offscreen UI simulation passed, including keyring failure/retry and hide/reopen.
- All nine Linux shell scripts passed Bash syntax validation.
Native Windows/Mint desktop, GPU, account sign-in and hardware checks retain the
limits described in FEATURE_STATUS.md and TEST_REPORT.md. This import does not
claim that a native Windows installer or Mint graphical login was exercised here.

