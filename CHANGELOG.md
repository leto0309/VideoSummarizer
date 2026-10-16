# Changelog

## 0.3.11 — 2026-10-16

Downloads ride out short network drops. When a transfer stops part-way, yt-dlp already resumes from the part saved on disk, but it gave up after 2 immediate retries; it now retries up to 10 times, waiting 1, 2, 4 ... up to 30 seconds in between. When a download still fails because the connection was interrupted, timed out or could not be made, the page now says the network was briefly unstable and to try again, instead of suggesting a yt-dlp update and a restart. Other platform errors keep the update advice. This was found on v0.3.10, where a Bilibili audio transfer stopped part-way and worked on the next try.

## 0.3.10 — 2026-10-15

The first-time setup window now lets you choose Simplified Chinese (the default), Traditional Chinese or English, and switching updates the window at once. The choice is saved as the page language. Setup progress, the network check, the GPU, yt-dlp and Whisper installers and the launchers all use it, as does the web page; changing the page language later changes them too. Their messages come from a new standard-library-only table, so they work before OpenCC is installed, and the Traditional Chinese text equals the page's own OpenCC conversion. The `update-ytdlp.bat` menu and the source edition's `install-gpu.bat` prompt moved into Python, so they follow the language.

Add README.en.md, an English README for the current version that links to this changelog for earlier releases. Both READMEs link to each other.

## 0.3.9 — 2026-10-14

Every dependency is now locked with hashes. `requirements.lock` pins all 61 packages of the main install, including the transitive ones that previously resolved to whatever was newest on the day of setup, and `requirements-gpu.lock` pins the 3 optional CUDA packages. Each package lists the SHA256 of its PyPI files for Windows x64 / CPython 3.11. First-time setup, `setup.bat`, GPU installation, the yt-dlp restore and CI install them with `--require-hashes`, so pip refuses any file that was not tested. The portable build makes the srt wheel from its hash-verified source archive and adds the wheel's hash to the packaged lock. `scripts/lock_requirements.py` regenerates the locks from `requirements.txt` and `requirements-gpu.txt`. A clean source install and a locally built portable package both completed a real first-time setup and summary with the locks.

The yt-dlp updater's completion message now says whether it updated or restored, and restore also returns any dependency the update changed to its locked version. It still asks to restart the computer, because closing the page does not stop the background service.

The frame and timeline prompts ask for plain text without headings. In a real run the 2B model still began its frame notes with "# 画面描述", so the report cleanup added in 0.3.8 remains what keeps the outline intact.

CI also runs ruff for errors such as undefined names and unused imports; this does not change the application.

## 0.3.8 — 2026-10-14

When a platform answers without any downloadable audio or video, the page now says so and explains what to do instead of showing the generic "check your network, local model and file permissions" message. Testing v0.3.7 found that Bilibili's risk control sometimes answers anonymous requests this way. The message says to try again later, run `update-ytdlp.bat` if it keeps failing, and that the tool never logs in or bypasses platform limits. The README FAQ has a matching entry. The Traditional Chinese wording avoids an OpenCC mis-conversion.

Model-written headings no longer break the report outline. A frame or timeline note's leading title (for example "# 画面描述", or an unrelated "# 电驴") is dropped, other headings become bold text, and level-one headings in the overall summary become level two. `metadata.json` keeps the model's original text.

Add `scripts/verify_release.py`, which checks a published release through the public GitHub API: checksum manifests against GitHub's digests, the full source ZIP, and the version, edition and base hashes of the Windows ZIPs read through HTTP Range requests. CONTRIBUTING describes running it after the release workflows finish.

## 0.3.7 — 2026-10-14

Add `update-ytdlp.bat`. When Bilibili or YouTube changes and downloads fail, it updates the bundled yt-dlp and yt-dlp-ejs from PyPI inside the application folder, or restores the versions tested with this release; it refuses to run while a summary task is active. The About section shows the installed yt-dlp version, and the readiness check accepts yt-dlp versions newer than the pin so an update does not trigger first-time setup again. The page now gives a GPU hint based on the computer: with an NVIDIA GPU and no GPU runtime it suggests `install-gpu.bat`; once the runtime is installed, speech recognition defaults to "Auto: CUDA → CPU".

Small fixes: hard-coded Chinese messages in the launchers, setup and native window are now Simplified Chinese, with a test that keeps Traditional characters out. Saved source addresses keep only the `p` and `v` query parameters, dropping share tracking such as `vd_source`, `share_source` and `si`. Removing model-written timestamps no longer rewrites ratios and scores such as 16:9 or 3:1. Append-only logs are renamed to `.1` above 2 MB, keeping one previous copy. CPU speech recognition uses as many threads as the computer has cores, up to eight, instead of a fixed four.

## 0.3.6 — 2026-10-13

The link field accepts text copied with a platform's share button, such as Bilibili's "【title】 https://www.bilibili.com/video/...". The first https:// link is taken from the pasted text and shown below the field before it is used; the HTTPS Bilibili / b23.tv / YouTube allowlist is unchanged, and only the first link is considered. Metadata and the report's source line keep only the link, not the pasted title.

When summary or language-version processing fails, the error message now appears below the "processing stopped" status instead of inside it, so it stays visible after the status collapses. The full traceback is still written to logs/app-errors.log. Tests that simulate failures now write that log to a temporary folder.

## 0.3.5 — 2026-10-12

First-time setup checks the download sites before it starts: PyPI, nodejs.org, GitHub, the Ollama model registry and Hugging Face. The progress window lists which sites answer and which ones this setup needs, and `check-network.bat` runs the same check at any time, saving `logs/network-check.json`. The check sends HEAD requests only and uploads nothing. When a dependency, Node.js, Ollama program or model download fails, the error ends with the site involved, what it provides and what to try, and that site is checked again.

Node.js and Ollama program downloads retry and resume from the partial file, and are installed only after the official SHA256 matches. Setup no longer downloads a Qwen model that is already present, so a copied `models/ollama` folder works without the model registry. The README now separates current instructions from historical release notes. These changes were not tested on mainland China networks; a reachable site does not guarantee that large downloads complete.

## 0.3.4 — 2026-10-12

Maintenance release; the application behaves the same as 0.3.3. The with-Whisper and with-Whisper + Ollama editions now record the SHA256 of the verified standard portable ZIP as `base_sha256` in `WHISPER_BUNDLE.json`. Version 0.3.3 and earlier recorded the `vocabulary.txt` hash there by mistake. The base ZIP and every Whisper file were already checksum-verified, so only this provenance field was wrong.

Remove the stale v0.2.1 defaults from the Whisper bundle builder: the release version comes from the application version, and the verified base SHA256 must be passed explicitly. Remove the obsolete manual v0.2.1 with-Whisper workflow; every release builds that edition in the Windows portable workflow. Add offline regression tests for the bundle metadata, builder arguments, workflow invocations and release documents.

## 0.3.3 — 2026-10-11

Show the running VideoSummarizer version below the page title. A localized About section identifies the source / standard Windows / Whisper / Whisper + Ollama package edition and links to that version's release notes. Simplified Chinese, Traditional Chinese and English labels follow the page-language selector. Reading version information is entirely local and does not download models or check for updates.

Use one application-code version shared by the page and all release builders. Refuse mismatched release tags and packaged application versions. Stamp the edition into each portable package while preserving Python and model provenance. The page keeps the running code version when build metadata is old, missing or damaged, shows an unknown edition and gives recovery advice. A downloaded ZIP's name and the latest GitHub release cannot replace the running version.

Add offline three-language page coverage, preservation of input/device settings, corrupt metadata and mixed-install regression cases, and version/edition checks executed inside every extracted Windows deliverable.

## 0.3.2

First-time setup skips optional CUDA wheels and defaults speech recognition to CPU int8. GPU acceleration can be installed separately with install-gpu.bat, bounded retries and a 20-minute installer deadline. The Windows progress window supports cancelling the installation process tree while preserving models, outputs and CPU readiness. Main Python dependency installation has progress, local cache and a 45-minute deadline. Other tool/model download stages keep their own network timeouts.

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
