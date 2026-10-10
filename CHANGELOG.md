# Changelog

## Unreleased

Default application UI, progress/errors, model instructions and generated reports now use Simplified Chinese. Normalize model-generated prose with OpenCC t2s while retaining original video titles, uploader names, URLs, subtitle SRT and verified timestamps. New output metadata records summary_language=zh-CN. Existing summaries and the published v0.2.1 archives are unchanged; a three-language selector is not included in this change.

## 0.2.1 — 2026-10-10

Additional Windows `with-whisper` download: unchanged v0.2.1 application and bundled Python plus verified public small-model files, official model card and original license. Users extract one ZIP into a new folder and launch the EXE; no source overlay or separate speech-model transfer is needed. Other first-launch dependencies and Ollama models still require downloads. A dedicated workflow loads the real bundled model offline and tests the extracted ZIP before upload. Standard source and Windows assets remain unchanged.

Prepare Whisper small before downloading subtitle-free audio or starting GPU/CPU workers. Model download failures now show a specific network/model preparation message, save details to logs/whisper-download.log and do not repeat the same download as a CPU fallback. Complete existing caches and flat offline model folders are used without a Hub request. Genuine CUDA errors still fall back to CPU.

First setup attempts to predownload Whisper; if its host is unreachable, subtitle-based use remains available with a warning. The web page shows speech-model readiness, and prepare-whisper.bat allows a separately consented predownload/retry. README documents copying an existing cache or official model files for offline transfer. Partial model files are preserved for retry and never advertised as complete. Added offline/cache, download failure and worker fallback regression tests.

## 0.2.0 — 2026-10-10

Windows x64 portable ZIP with checksum-verified, bundled CPython 3.11.17 and a native VideoSummarizer.exe progress window. Users no longer install system Python. The first launch requests consent and automatically installs video/AI dependencies, portable tools and the default Ollama model inside the application directory. No global PATH changes or paid/cloud API.

Bookmark installation and startup scripts now recognize the bundled interpreter. Failed setup is not marked complete, and retry preserves models/outputs. Source downloads remain available. CI tests the extracted portable archive using its interpreter and native EXE with system Python absent from PATH, including HTTP health and application import. It does not automate the desktop window or perform model inference on every GPU.

## 0.1.0 — 2026-10-10

Initial Windows source preview. Subtitle-first Bilibili / b23.tv / YouTube processing; faster-whisper CUDA with CPU fallback; local Qwen3-VL summaries; optional decoded-frame PTS analysis; per-task temp cleanup and retained Markdown/SRT/metadata.

Includes startup progress and error logs, disabled Streamlit first-run email prompt, optional current-user bookmark URI launcher, pinned direct Python dependencies, Windows unit CI, MIT license and third-party notices.

This is a source distribution requiring Python 3.11, not a standalone EXE. Clean-device GPU inference is not universally verified. No models, downloaded media or personal logs are included.
