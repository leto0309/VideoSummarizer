# Changelog

## 0.3.1

Add a `windows-x64-with-whisper-ollama.zip` edition combining this release's verified Python/Whisper package with the complete official Ollama 0.40.2 Windows amd64 ZIP. Pin and verify the upstream ZIP SHA256; preserve every DLL and component notice and add the upstream Ollama MIT license. Stream archive creation to limit memory use, reject unsafe paths and private base files, check ZIP CRC and the GitHub 2 GiB asset limit, and provide archive/individual-file provenance plus SHA256 manifest.

First setup uses the bundled Ollama and skips its GitHub download. This addresses the Ollama ZIP connection interruption reported during v0.2.1 installation. Other Python dependencies, FFmpeg, Node.js, optional CUDA wheels and Qwen weights still download after consent; this edition is not fully offline. Keep all v0.3.0 language features and leave previous downloads unchanged.

Release CI tests the actual extracted Ollama on an isolated loopback port with no model download, verifies each bundled file, loads the real Whisper small offline on CPU, runs application tests and the native launcher without PATH Python, and uploads only after success. Add regression coverage that forbids Ollama download requests during setup when the binary is present.

## 0.3.0 — 2026-10-10

Simplified Chinese is the default. Application UI, progress, friendly error messages and summary generation support Simplified Chinese, Traditional Chinese and English. Page and summary languages can be selected separately, with the summary following the page by default. Stable widget keys preserve URL/device/permission settings when switching languages; project-local preferences survive restart.

Saved summaries can generate additional language versions from retained prose and notes, without downloading the video again. Chinese script conversion uses OpenCC; English conversion uses the same local Qwen model. Originals and SRT remain untouched. Version reports/metadata publish together and are cached for immediate reuse. Preserve original titles, authors, URLs, verified timestamps and frame hashes. Translation uses the same task lock, bounded context and temp retention/cleanup rules as original processing.

Release downloads include source, bundled-Python Windows and bundled-Python-with-Whisper Windows editions, SHA256 manifests and upstream notices. Test extracted Windows packages, native startup without PATH Python, all languages and real offline Whisper CPU loading before uploading. Other dependencies and the summary model still download after consent; no paid API or Ollama cloud. Existing v0.2.1 archives are unchanged.

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
