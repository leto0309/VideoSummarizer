# Changelog

## 0.2.0 — 2026-10-10

Windows x64 portable ZIP with checksum-verified, bundled CPython 3.11.17 and a native VideoSummarizer.exe progress window. Users no longer install system Python. The first launch requests consent and automatically installs video/AI dependencies, portable tools and the default Ollama model inside the application directory. No global PATH changes or paid/cloud API.

Bookmark installation and startup scripts now recognize the bundled interpreter. Failed setup is not marked complete, and retry preserves models/outputs. Source downloads remain available. CI tests the extracted portable archive using its interpreter and native EXE with system Python absent from PATH, including HTTP health and application import. It does not automate the desktop window or perform model inference on every GPU.

## 0.1.0 — 2026-10-10

Initial Windows source preview. Subtitle-first Bilibili / b23.tv / YouTube processing; faster-whisper CUDA with CPU fallback; local Qwen3-VL summaries; optional decoded-frame PTS analysis; per-task temp cleanup and retained Markdown/SRT/metadata.

Includes startup progress and error logs, disabled Streamlit first-run email prompt, optional current-user bookmark URI launcher, pinned direct Python dependencies, Windows unit CI, MIT license and third-party notices.

This is a source distribution requiring Python 3.11, not a standalone EXE. Clean-device GPU inference is not universally verified. No models, downloaded media or personal logs are included.
