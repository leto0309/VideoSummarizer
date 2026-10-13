# Contributing

Use Python 3.11 on Windows x64. Install requirements.txt in a virtual environment, then run `python -m unittest discover -s tests -v` from the repository root. Tests use local synthetic or mocked inputs and do not require models, platform credentials or a GPU. CI also runs ruff with the rules in `ruff.toml`, which catch errors such as undefined names and unused imports but not formatting; run it locally with `pip install ruff==0.16.9` and `ruff check .`.

For manual integration checks, use media you may lawfully process. Verify subtitle timestamps, a no-subtitle CPU transcription, CUDA fallback where available, decoded frame PTS, preserved output files, and cleanup only of marked project temp directories. Never claim unit tests prove a live platform download or model inference.

When reporting a bug, include the app version, Python version, operating system, GPU/VRAM if relevant, and the error. Redact local paths, usernames, signed URLs, credentials and private media before uploading logs. Do not upload outputs/, temp/, models/, tools/ or .venv/.

Before releases, pin direct dependencies to tested versions, run Windows CI, review LICENSE and third-party notices, and inspect the complete source archive manifest. Public releases must never contain personal bookmark-settings.json or pipeline ownership/PID files.

After the Source release and Windows portable release workflows finish, run `python scripts/verify_release.py vX.Y.Z`. It uses the public GitHub API without credentials and checks the published files. Each checksum manifest must match GitHub's asset digest. The full source ZIP must match its digest, pass its CRC check and carry the tagged version. Each Windows ZIP is read through HTTP Range requests: its version and edition must match, `base_sha256` in both Whisper editions must be the published standard ZIP, and the Ollama edition must be built on the published with-Whisper ZIP. It prints a JSON report and exits with status 1 on any problem.
