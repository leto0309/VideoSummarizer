# VideoSummarizer

[简体中文](README.md) | English

A free, local video summarizer for Windows: Bilibili / b23.tv / YouTube, subtitles first, with optional frame analysis. Speech recognition and summarization both run on your own computer; no paid API or Ollama cloud is used.

The web page can be switched to English with the **Page language / Language** selector, and the summary language can be chosen separately (Simplified Chinese, Traditional Chinese or English). Simplified Chinese is the default. The first-time setup window and the prompts of the `.bat` helper files are only in Simplified Chinese; this README explains what they do.

## v0.3.9: every package installed during setup is tested and verified

Download the [v0.3.9 edition with Whisper + Ollama](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.9/VideoSummarizer-v0.3.9-windows-x64-with-whisper-ollama.zip) and extract all of it into a new folder you can write to. Stop the old version's services or restart Windows, then double-click `VideoSummarizer.exe`. The page shows the running version below the title (`Running version: v0.3.9` in English, `当前运行版本：v0.3.9` in Chinese).

First-time setup downloads the Python dependencies from PyPI. Previously only the 9 direct dependencies were pinned; the packages they pulled in were whatever was newest that day, so a change upstream could break setup. Now all 61 packages are pinned to tested versions and the SHA256 of every file is checked; pip refuses anything that does not match. The 3 packages of the optional GPU acceleration are locked the same way.

When `update-ytdlp.bat` finishes, it now says whether it updated or restored the download component. Restore puts yt-dlp, and any dependency the update changed, back to the tested versions.

Still included: the clear message when Bilibili temporarily withholds a video and the tidier report outline from v0.3.8; `update-ytdlp.bat` and the GPU hint from v0.3.7; share-text links from v0.3.6; the network check (`check-network.bat`) and resumable downloads from v0.3.5; and CPU int8 by default, no CUDA download during first-time setup, and the separate `install-gpu.bat`. The Whisper + Ollama edition still downloads the remaining Python dependencies, Node.js and the Qwen summary model after you agree on first start; it is not a fully offline package. See "Upgrading" below.

The rest of this README describes the current version. Notes for earlier releases are in [CHANGELOG.md](CHANGELOG.md) (see "Release history" at the end).

## Download and installation

### Windows portable edition (recommended)

[Releases](https://github.com/leto0309/VideoSummarizer/releases) offers three Windows x64 portable editions. All include Python 3.11, so no Python installation is needed:

| Package | Size (approx.) | Includes |
|---|---|---|
| `windows-x64-with-whisper-ollama.zip` (recommended) | 1.97 GB | Python, the Whisper small speech model, the official Ollama program |
| `windows-x64-with-whisper.zip` | 500 MB | Python, the Whisper small speech model |
| `windows-x64.zip` | 49 MB | Python |

None of them is fully offline. On first start you are asked whether to download the remaining Python dependencies (including FFmpeg), Node.js, the Ollama program or Whisper model if the package lacks them, and the Qwen summary model; together this can be several GB. Keep at least 15 GB of free disk space. Before downloading, the progress window lists which download sites can be reached; on an unreliable network you can run `check-network.bat` first.

1. Download the ZIP; if you like, check its SHA256 with the `*_SHA256SUMS.txt` file on the release page. Extract it completely into a new folder you can write to; do not run it from inside the ZIP.
2. Double-click `VideoSummarizer.exe` and agree; the progress window sets everything up. Python dependency installation shows progress, has a 45-minute overall limit, and can be cancelled with the 「取消配置」 (Cancel setup) button. Cancelling or failing keeps existing models and summaries; open the program again to retry.
3. When setup finishes, <http://127.0.0.1:8501/> opens. Double-clicking the same EXE later starts or reuses this folder's background service. Closing the web page or the progress window does not stop the background service.

The portable edition does not change the system PATH, does not register a system Python and needs no administrator rights. First-time setup skips the optional CUDA runtime, and speech recognition uses CPU int8. Logs are in `logs/`; the setup logs are `logs/install.log` and `logs/desktop.log`.

### Optional: Whisper GPU acceleration

The page shows a hint that depends on the computer: if it finds an NVIDIA graphics card but GPU acceleration is not installed, it suggests running `install-gpu.bat`.

To accelerate speech recognition on an NVIDIA GPU, double-click `install-gpu.bat` after first-time setup is complete and while no summary is running, and agree to the download (over 1 GB). The window shows download progress, has a 20-minute overall limit and can be cancelled. Failure, timeout or cancelling does not affect CPU mode and does not delete models or summaries.

After installation, restart the program. **Speech recognition device** then defaults to **Automatic: CUDA → CPU** (without the GPU runtime it defaults to **CPU int8 only**). A successful installation does not guarantee the graphics card is compatible; if transcription fails it falls back to the CPU automatically. Newer cards such as the RTX 50 series have not been verified. Whether Ollama uses the GPU is decided by Ollama itself and is not affected by this setting.

### Upgrading

1. Extract the new version completely into a **new** folder. Do not overwrite the old folder, and do not copy individual new files into it.
2. Stop the old version's services or restart Windows. Both versions use ports `8501` / `11435` and cannot run at the same time.
3. To keep models and earlier summaries, copy the whole `models` and `outputs` folders. Do not copy `portable-ready.json`, `logs`, `PORTABLE_BUILD.json`, `runtime`, `.venv` or old patch files.
4. If you used the Chrome bookmark, run `remove-bookmark.bat` in the old folder first, then `install-bookmark.bat` in the new folder; a handler registered to the old folder is not overwritten automatically.
5. After opening the new version, check the running version below the page title. It shows the version actually running in the background; if it is still the old one, the old service is still running.

### Developers: source edition (requires Python 3.11)

1. Download `source.zip` from Releases and extract it into a folder you can write to.
2. Install 64-bit Python 3.11 from the [official Python website](https://www.python.org/downloads/windows/).
3. Double-click `setup.bat` and agree to the project-local downloads. It creates `.venv`, installs the Python dependencies, downloads Node.js, Ollama, the default Qwen summary model and Whisper small, and runs diagnostics. It does not install the CUDA runtime.
4. Double-click `start.bat`, wait until it reports success, then open <http://127.0.0.1:8501/>. Keep the startup window open.
5. For GPU acceleration, use `install-gpu.bat` as well.

Running `setup.bat`, `start.bat` or `install-gpu.bat` inside a portable folder hands over to `VideoSummarizer.exe`. The installers do not install the system CUDA Toolkit or change the global PATH.

## Requirements and models

- Target system: Windows 10 22H2 / Windows 11 x64. Other systems are not verified.
- 16 GB of RAM and at least 15 GB of free disk space are recommended; this is a recommendation, not a verified minimum.
- Speech recognition: Whisper `small`, CPU `int8` by default. With GPU acceleration installed and Automatic selected, a compatible NVIDIA GPU uses CUDA `int8_float16` and falls back to the CPU on failure. Long videos can be slow on the CPU.
- Whisper small is about 464 MiB. The editions with Whisper include it; otherwise it is downloaded from the official Hugging Face repository into `models/whisper`. A complete local model is used directly, without another online check during transcription.
- Summary model: Ollama `qwen3-vl:4b-instruct`; `qwen3-vl:2b-instruct` is used when no NVIDIA GPU is found or it has less than 6000 MiB of video memory. Speed depends on the hardware.
- The context is 4096 tokens; long subtitles are summarized in parts and then merged. Whisper and Ollama run one after the other, and only one summary task runs at a time.
- Local endpoints: web page `127.0.0.1:8501`, the project's Ollama `127.0.0.1:11435`; neither is reachable from other computers.

Automated tests check the program logic. The release process also runs the tests and a launcher self-test inside each extracted Windows package and loads Whisper offline. None of this runs summary-model inference or downloads platform videos. An early version was verified end to end (subtitles, CUDA / CPU transcription and frame timestamps) on one Windows PC with an RTX 3050 Laptop GPU (4 GB) and 16 GB of RAM; that does not mean every device or every video works.

## Summaries, outputs and cleanup

Manual subtitles are read first, then automatic subtitles; only when there are none is the audio downloaded and transcribed with Whisper. Optionally a low-resolution video is downloaded and FFmpeg extracts about 8 evenly spaced frames, timed by the PTS of the actually decoded frames.

Successful outputs are saved in `outputs/<date-time>_<task ID>/`:

- `summary.md`: video information, summary, key points, explained concepts, the subtitle timeline and the frame descriptions.
- `subtitles.srt`: the original subtitles or the transcription, with source timestamps for checking.
- `metadata.json`: source, model, device, frame PTS, SHA256 and analysis details.
- `translations/<language code>/`: other language versions created on the page; the original summary and SRT are not rewritten.

Once the outputs are written, the task's video, audio and screenshots are deleted; a failed task's temporary files are kept for 24 hours. Project temporary storage is limited to 5 GB, and only task folders carrying the project's marker are cleaned; models and other files are never deleted.

Speech recognition and summaries can be wrong, especially for names, technical terms and poor audio. Name corrections must be supported by source material, and a summary does not replace checking the original video. Frame sampling does not cover the whole video.

## Chrome launch bookmark (optional)

1. After first-time setup (the portable edition's first start, or `setup.bat` for the source edition), double-click `install-bookmark.bat` to register the link handler for the current Windows user.
2. In Chrome's bookmark manager, add a bookmark with the URL `videosummarizer://open`.
3. When you click the bookmark, confirm opening the external application. The launcher is Python, so the prompt may mention Python.

If the service is already running, the page opens directly; otherwise it starts in the background and waits until ready. A cold start can take about two minutes; progress is logged in `logs/bookmark.log` and `logs/startup.log`. If Chrome does not accept the protocol bookmark, bookmark the project's `bookmark.html` and use its button.

The bookmark is not autostart, and closing the page does not stop the background service. To remove the registration, run `remove-bookmark.bat`; models and summaries are kept. The launcher opens the system default browser.

## Troubleshooting

### First-time setup download fails / checking the network

First-time setup downloads from several sites; if any one cannot be reached, setup stops:

| Site | Downloads | Already included in |
|---|---|---|
| PyPI (pypi.org, files.pythonhosted.org) | Python dependencies (including FFmpeg), optional CUDA runtime | none |
| Node.js website (nodejs.org) | Node.js | none |
| GitHub | the Ollama program | the Whisper + Ollama edition |
| Ollama model library (registry.ollama.ai) | the Qwen summary model | none |
| Hugging Face | the Whisper speech model | both editions with Whisper |

1. Double-click `check-network.bat` in the program folder. It tests whether each site can be reached and saves the result to `logs/network-check.json`. It only sends connection tests, uploads nothing, and works before first-time setup too. The portable edition shows the same check automatically when setup starts and marks which sites this setup needs.
2. When setup fails, the end of the progress window names the site, what it provides and what to try, and checks that site again. The full record is in `logs/desktop.log` and `logs/install.log`.
3. Open `VideoSummarizer.exe` again to retry: Python dependencies reuse `tools/pip-cache`, the Node.js and Ollama downloads continue from the part already downloaded, and Ollama resumes the Qwen model itself.
4. If GitHub cannot be reached, use the Whisper + Ollama edition; if Hugging Face cannot be reached, use an edition with Whisper.
5. If the Ollama model library cannot be reached, complete setup on a computer that can download, then copy the whole `models/ollama` folder to the same place in this computer's program folder; setup skips the download when the model is already present.

"Can be reached" only means a connection works; it does not guarantee that large files download completely.

### Whisper download timeout / WinError 10060 / LocalEntryNotFoundError

The speech model could not be downloaded and there is no complete local copy. This is not a CUDA failure, and switching to the CPU does not help. The page opening does not mean every model has been downloaded. Videos with subtitles can still be processed.

1. If the network cannot reach Hugging Face, the simplest fix is an edition with Whisper included.
2. Make sure the [official small model page](https://huggingface.co/Systran/faster-whisper-small) opens, then double-click `prepare-whisper.bat` in the program folder and agree to the download. The reason for a failure is logged in `logs/whisper-download.log`, and downloaded parts are kept for a retry.
3. If this computer has no internet access, do step 2 on a computer that can download, close the program and copy **the whole `models/whisper` folder** to the same place in this computer's program folder. If the source cache uses symbolic links, copy the actual file contents.
4. You can also download `model.bin`, `config.json`, `tokenizer.json` and `vocabulary.txt` (or `vocabulary.json`) from the official model page into `models/whisper/small/`, plus `preprocessor_config.json` when upstream provides it. It must be the faster-whisper CTranslate2 model; OpenAI's original `.pt` files do not work.
5. Run `prepare-whisper.bat` again. With complete local files it passes without downloading, and the page's **Whisper model status / Download help** section shows whether the model is ready.

### Other problems

- **Nothing happens on first start**: look for the browser's "open external application / Python" prompt; while Ollama initializes, check `logs/startup.log`.
- **Port already in use**: check whether another folder of this project or another program is running. An unknown Ollama service is refused, and the program never ends other programs' processes.
- **CUDA fails**: transcription falls back to the CPU automatically. For diagnostics, run `runtime\python.exe diagnostics.py` (portable) or `.venv\Scripts\python.exe diagnostics.py` (source) in the program folder; the result is also saved in `logs/diagnostics.json`. Remove private data and local paths before reporting a problem.
- **Platform download fails**: after Bilibili or YouTube changes, the download component yt-dlp may need an update. Double-click `update-ytdlp.bat` in the program folder and choose U (更新, update) to install the newest version from PyPI (only into this program folder), then restart the computer and try again. If things get worse after updating, run it again and choose R (恢复, restore) to return to the version tested with this release. The current version is shown in the page's **About VideoSummarizer** section. Updating is not possible while a summary is running. When a video needs login or payment, asks for verification or is otherwise restricted, the tool stops and does not bypass it.
- **"The platform did not offer any downloadable audio or video this time"**: Bilibili sometimes temporarily limits access without login, and then even the same video yields no audio or video. Try again later (minutes to hours); retrying many times in a short period may make the limit last longer. If it keeps failing, update the download component with `update-ytdlp.bat` as in the previous item. This tool does not read browser cookies, log in or bypass platform limits.
- **Still the old version after upgrading**: see "Upgrading" above; stop the old service first, then start from the new folder.

## Development and contributing

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.lock
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests do not download AI models. Installation and real inference need separate checks; see [CONTRIBUTING.md](CONTRIBUTING.md).

## Scope and privacy

Only process content you are legally allowed to access. The tool does not read browser cookies, does not use account passwords, and does not bypass DRM, payment, login, verification or regional restrictions. The downloader accepts only HTTPS Bilibili / b23.tv / YouTube links.

Ollama cloud is disabled; subtitles and frames are sent only to the project's own local Ollama. Video platforms, GitHub, PyPI, Node.js, the Ollama model library and Hugging Face still receive the necessary download requests. The first download of programs and models always requires your consent.

The project's code is licensed under [MIT](LICENSE). Third-party programs, packages and models keep their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The source ZIP contains no third-party binaries or model weights. The Windows portable packages also contain CPython with its upstream licenses, and the editions with Whisper / Ollama contain that model or program with its license; none contain downloaded videos.

## Release history

Notes for each earlier release are in [CHANGELOG.md](CHANGELOG.md). The Chinese [README.md](README.md) also keeps the release notes as they were published at the time; they apply only to those versions.
