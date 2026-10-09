# Third-party components

The MIT license in LICENSE applies to VideoSummarizer's own source code. It does not replace the licenses of dependencies or model weights. The source release contains no vendor binaries or model weights; setup downloads them separately from their upstream providers.

| Component | Upstream / license reference |
| --- | --- |
| Python | https://docs.python.org/3/license.html |
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

Other Python dependencies retain their own license files in the installed environment. Use upstream metadata for the specific versions installed. Some FFmpeg builds contain GPL components; verify the actual build and meet its distribution obligations before bundling its binaries in a future installer. This repository does not promise that arbitrary repackaged dependencies can all be distributed under MIT.
