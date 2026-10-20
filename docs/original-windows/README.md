# Jarvis Fresh

A file-first Windows 11 x64 local assistant engineering preview. Start with
`START_HERE.txt` and `SETUP_STEP_BY_STEP.md`; use `FEATURE_STATUS.md` to distinguish
implemented adapters from verified native capabilities.

The app uses Python, Qt Widgets and local Ollama. Its core separates conversation,
permission decisions, file transactions, tools, accounts, observation, scheduling,
voice and paired-device transport. Credentials are never deliberately provided
to the language model. Code execution is owner-approved and **not sandboxed**.

Run tests from the project root with `python scripts/run_tests.py`. UI simulation:
`python scripts/ui_smoke.py` (Qt required). Generated-audio test:
`python scripts/voice_smoke.py` (voice dependencies and model assets required).
Actual results and their platform are under `test-results`.

The broader source-review specification is included for traceability. Requirements
in that specification are targets, not assertions that this preview implements all
of them. No old personal credentials, conversations, account identifiers, or complete
old runtime archives are included in this distribution.
