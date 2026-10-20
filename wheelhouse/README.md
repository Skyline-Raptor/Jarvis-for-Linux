# Optional offline wheel cache

GitHub source downloads do not bundle third-party Python wheels. The installers
use PyPI with the checked-in version constraints when this directory has no wheels.
If you populate it with a complete compatible wheel set, they use offline mode.

Use the release's supported platform and Python version when building a cache:
`python -m pip wheel -r requirements.txt -r requirements-voice.txt -c constraints.txt --wheel-dir wheelhouse`.
On Linux also include `uv==0.13.4`; on Windows include `pip==26.2.1`.
Linux requires Python 3.12. Windows supports 3.11/3.12, so build a separate set
for each interpreter version you intend to use. Do not copy Linux native wheels
into Windows, or Windows wheels into Linux. Model weights install separately.
