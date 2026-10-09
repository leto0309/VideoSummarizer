# Contributing

Use Python 3.11 on Windows x64. Install requirements.txt in a virtual environment, then run `python -m unittest discover -s tests -v` from the repository root. Tests use local synthetic or mocked inputs and do not require models, platform credentials or a GPU.

For manual integration checks, use media you may lawfully process. Verify subtitle timestamps, a no-subtitle CPU transcription, CUDA fallback where available, decoded frame PTS, preserved output files, and cleanup only of marked project temp directories. Never claim unit tests prove a live platform download or model inference.

When reporting a bug, include the app version, Python version, operating system, GPU/VRAM if relevant, and the error. Redact local paths, usernames, signed URLs, credentials and private media before uploading logs. Do not upload outputs/, temp/, models/, tools/ or .venv/.

Before releases, pin direct dependencies to tested versions, run Windows CI, review LICENSE and third-party notices, and inspect the complete source archive manifest. Public releases must never contain personal bookmark-settings.json or pipeline ownership/PID files.
