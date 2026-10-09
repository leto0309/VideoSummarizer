# Third-party components

The MIT license in LICENSE applies to VideoSummarizer's own source code. It does not replace the licenses of dependencies or model weights. The source release contains no vendor binaries or model weights. The Windows portable release additionally redistributes Astral python-build-standalone CPython 3.11.17 (release 20261009), preserving the upstream LICENSE and component notices inside runtime/, and a pure-Python srt 3.5.3 wheel with its MIT license in wheels/. Other application dependencies, tools and model weights are downloaded on the user's machine after consent; they are not bundled in the portable ZIP.

Standalone runtime provenance: https://github.com/astral-sh/python-build-standalone/releases/tag/20261009 . Python is under the PSF license, with additional bundled components retaining their own notices. See https://github.com/astral-sh/python-build-standalone and the included runtime license files. The application launcher is project-authored C# targeting the .NET Framework already present in supported Windows versions; no .NET installer is redistributed.

| Component | Upstream / license reference |
| --- | --- |
| Python | https://docs.python.org/3/license.html |
| srt (prebuilt pure-Python wheel in portable ZIP) | https://github.com/cdown/srt/blob/master/LICENSE |
| Streamlit | https://github.com/streamlit/streamlit/blob/develop/LICENSE |
| yt-dlp and yt-dlp-ejs | https://github.com/yt-dlp/yt-dlp#license and https://github.com/yt-dlp/ejs |
| faster-whisper | https://github.com/SYSTRAN/faster-whisper/blob/master/LICENSE |
| CTranslate2 | https://github.com/OpenNMT/CTranslate2/blob/master/LICENSE |
| FFmpeg / imageio-ffmpeg | https://ffmpeg.org/legal.html and https://github.com/imageio/imageio-ffmpeg/blob/main/LICENSE |
| Ollama | https://github.com/ollama/ollama/blob/main/LICENSE |
| Node.js | https://github.com/nodejs/node/blob/main/LICENSE |
| CUDA runtime wheels | NVIDIA package notices and https://docs.nvidia.com/cuda/eula/ |
| Whisper weights | https://github.com/openai/whisper/blob/main/LICENSE and the actual Hugging Face model repository |
| Qwen3-VL weights | https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct and https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct |
| OpenCC reimplementation | https://github.com/yichen0831/opencc-python/blob/master/LICENSE |

Other Python dependencies retain their own license files in the installed environment. Use upstream metadata for the specific versions installed. Some FFmpeg builds contain GPL components; FFmpeg, PyAV and their codec libraries are downloaded from PyPI during first configuration, rather than redistributed in this project's ZIP. Future bundles of those components must meet their actual source and licensing obligations. This repository does not promise that arbitrary repackaged dependencies can all be distributed under MIT.
