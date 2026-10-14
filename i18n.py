"""Translate application-owned text before inserting original source evidence."""
from functools import lru_cache
from opencc import OpenCC

LANGUAGES = ('zh-CN', 'zh-TW', 'en')
DEFAULT_LANGUAGE = 'zh-CN'
LANGUAGE_NAMES = {'zh-CN': '简体中文', 'zh-TW': '繁體中文', 'en': 'English'}
TEXT = {
 'app_version': ('当前运行版本：{version}', 'Running version: {version}'),
 'about': ('关于 VideoSummarizer', 'About VideoSummarizer'),
 'app_edition': ('安装包类型：{edition}', 'Package edition: {edition}'),
 'edition_source': ('源代码版', 'Source edition'),
 'edition_windows-x64': ('Windows 标准版（内含 Python）', 'Windows standard edition (Python included)'),
 'edition_windows-x64-with-whisper': ('Windows 内含 Python + Whisper 版', 'Windows edition with Python + Whisper'),
 'edition_windows-x64-with-whisper-ollama': ('Windows 内含 Python + Whisper + Ollama 版', 'Windows edition with Python + Whisper + Ollama'),
 'edition_unknown': ('未知', 'Unknown'),
 'release_notes': ('查看此版本的更新说明', 'View release notes for this version'),
 'running_version_help': ('这里显示当前后台运行的版本。下载新版后，请停止旧版服务，再打开新版文件夹中的程序。', 'This is the version running in the background. After downloading an update, stop the old services and launch the program from the new folder.'),
 'version_mismatch': ('安装包记录与当前运行代码的版本不一致。请将发布包完整解压到新文件夹，然后停止旧版服务并打开新版。', 'Package metadata and running code versions differ. Fully extract the release into a new folder, stop the old services, and launch the new copy.'),
 'version_unavailable': ('无法确认安装包类型。当前运行代码的版本显示在标题下；请完整解压发布包到新文件夹。', 'The package edition could not be verified. The running code version is shown below the title. Fully extract the release into a new folder.'),
 'title': ('本机视频摘要', 'Local Video Summarizer'),
 'language': ('页面语言 / Language', 'Page language / Language'),
 'summary_language': ('摘要语言', 'Summary language'),
 'follow': ('跟随页面语言', 'Follow page language'),
 'caption': ('免费本机 AI · 字幕优先 · 单一任务序列处理', 'Free local AI · Subtitles first · One task at a time'),
 'gpu': ('{name}｜VRAM {memory} MiB｜', '{name} | VRAM {memory} MiB | '),
 'gpu_cpu': ('Whisper small 使用 CPU int8 转录。', 'Whisper small transcribes with CPU int8.'),
 'gpu_suggest': ('Whisper 目前用 CPU int8 转录，长视频较慢。这张显卡可以加速：在没有摘要任务时双击软件文件夹里的 install-gpu.bat（需下载超过 1 GB），完成后重启程序。', 'Whisper currently transcribes with CPU int8, which is slow for long videos. This graphics card can speed it up: when no summary is running, double-click install-gpu.bat in the application folder (downloads over 1 GB), then restart the program.'),
 'gpu_ready': ('GPU 加速已安装，「语音识别运算」默认使用「自动：CUDA → CPU」；CUDA 失败时会自动改用 CPU。', 'GPU acceleration is installed, so speech recognition defaults to Automatic: CUDA → CPU. It falls back to CPU if CUDA fails.'),
 'ytdlp_version': ('视频下载组件 yt-dlp：{version}', 'Video download component yt-dlp: {version}'),
 'no_gpu': ('未检测到 NVIDIA GPU', 'No NVIDIA GPU detected'),
 'model_status': ('Whisper 语音模型状态 / 下载失败处理', 'Whisper model status / Download help'),
 'model_ready': ('Whisper small 文件已就绪；转录使用本机文件，不再连接下载。', 'Whisper small is ready. Transcription uses local files without another download.'),
 'model_missing': ('Whisper small 尚未准备完成。有字幕的视频可直接处理；无字幕视频需先下载语音模型。', 'Whisper small is not ready. Videos with subtitles can be processed; other videos need the speech model first.'),
 'model_help': ('双击 prepare-whisper.bat 下载（约 464 MiB）。无法连接 Hugging Face 时，可复制另一台电脑的 models/whisper 文件夹，或将官方文件放到 models/whisper/small。详见 README。', 'Run prepare-whisper.bat (about 464 MiB). If Hugging Face is unreachable, copy models/whisper from another computer or place the official files in models/whisper/small. See README.'),
 'url': ('Bilibili、b23.tv 或 YouTube 链接', 'Bilibili, b23.tv or YouTube URL'),
 'url_extracted': ('已从粘贴的文字中取出链接，将使用：{url}', 'Using the link found in the pasted text: {url}'),
 'visual': ('加入约 8 张代表画面的本机分析（需额外下载低分辨率视频）', 'Analyze about 8 frames locally (requires a low-resolution video download)'),
 'model': ('本机视觉语言模型', 'Local vision-language model'),
 'mode': ('语音识别运算', 'Speech recognition device'),
 'auto': ('自动：CUDA → CPU', 'Automatic: CUDA → CPU'), 'cpu': ('只用 CPU int8', 'CPU int8 only'),
 'lawful': ('我确认有权访问和处理此视频；工具不绕过登录、付费、DRM 或平台限制。', 'I have permission to process this video. This tool does not bypass login, payment, DRM or platform restrictions.'),
 'consent': ('请先确认你有权处理此视频。', 'Please confirm that you have permission to process this video.'),
 'start': ('开始生成摘要', 'Generate summary'),
 'processing': ('处理中，请保持页面开启', 'Processing. Please keep this page open.'),
 'done': ('完成', 'Complete'), 'stopped': ('处理停止', 'Processing stopped'),
 'failure_temp': ('失败暂存保留 24 小时；下次任务自动清理过期的项目暂存。', 'Failed task files are retained for 24 hours. Expired project task files are cleaned on the next task.'),
 'saved': ('产出已保留：{folder}', 'Outputs saved: {folder}'), 'download': ('下载 {filename}', 'Download {filename}'),
 'preferences_failed': ('无法保存语言偏好，本次选择仍可使用。请检查软件文件夹的写入权限。', 'Language preferences could not be saved. Your current selection still works. Check application-folder write permissions.'),
 'existing_language': ('当前摘要语言：{language}。页面切换不会自动改写已有摘要。', 'Displayed summary language: {language}. Page language changes do not rewrite saved summaries.'),
 'make_version': ('生成 {language} 版本', 'Create {language} version'),
 'version_help': ('使用保留的摘要与笔记；保留原版和 SRT。英文转换需本机模型处理，完成后可快速切换。', 'Uses retained summaries and notes; preserves the original and SRT. English translation needs the local model. Completed versions can be switched immediately.'),
 'checking': ('检查本机模型与视频访问权限', 'Checking the local model and video access'),
 'subtitles': ('寻找可公开取得的字幕', 'Looking for publicly accessible subtitles'),
 'speech_check': ('无字幕，检查 Whisper small（首次可能需要下载）', 'No subtitles: checking Whisper small (first use may require a download)'),
 'model_downloading': ('下载 Whisper small（约 464 MiB），完成后可离线转录', 'Downloading Whisper small (about 464 MiB) for offline transcription'),
 'transcribing': ('下载音频并使用 Whisper 转录', 'Downloading audio and transcribing with Whisper'),
 'extracting': ('下载低分辨率视频并截取约 8 张代表画面', 'Downloading low-resolution video and extracting about 8 frames'),
 'frame_progress': ('本机视觉分析 {index}/{total}', 'Local frame analysis {index}/{total}'),
 'chunk_progress': ('字幕分段摘要 {index}/{total}', 'Subtitle segment summary {index}/{total}'),
 'merging': ('合成 {language} 摘要与可核对时间轴', 'Creating the {language} summary and verifiable timeline'),
 'cleaned': ('摘要、SRT、metadata 已保存，媒体暂存已删除', 'Summary, SRT and metadata saved; temporary media deleted'),
 'busy': ('另一个任务正在处理，请等待完成；全程只允许一个任务。', 'Another task is running. Please wait; only one task can run at a time.'),
 'source': ('来源', 'Source'), 'author': ('作者', 'Author'), 'duration': ('长度', 'Duration'),
 'subtitle_source': ('字幕来源', 'Subtitle source'), 'local_model': ('本机模型', 'Local model'),
 'unknown': ('未知', 'Unknown'), 'video': ('视频', 'Video'), 'references': ('对照文件', 'Reference files'),
 'timeline': ('字幕时间轴（来源时间）', 'Subtitle timeline (source timestamps)'),
 'frames': ('代表画面（FFmpeg 实际帧 PTS）', 'Representative frames (actual FFmpeg frame PTS)'),
 'frame_retained': ('截图已清理；时间、帧 SHA256 与描述保留于 metadata，可回原视频核对。', 'Screenshots have been deleted. Timestamps, frame SHA256 hashes and descriptions remain in metadata for comparison with the original video.'),
 'limitations': ('核对与限制', 'Verification and limitations'),
 'limit_model': ('模型理解可能有误，请对照 SRT 与原视频。', 'Model interpretations may be wrong. Compare the SRT and original video.'),
 'limit_frames': ('约 8 张取样画面不代表完整视觉内容。', 'About 8 sampled frames do not cover all visual content.'),
 'limit_no_frames': ('未分析画面。', 'Frames were not analyzed.'),
 'time_placeholder': ('（时间由下列来源索引提供）', '(timestamps are provided by the source index below)'),
 'note_subtitle': ('字幕来源：', 'Subtitle evidence: '), 'note_frame': ('画面可见资料：', 'Visible frame evidence: '),
 'frame_prompt': ('描述可见文字、物件或图表，约 150 字，直接写描述，不加标题。字幕仅作辅助，不可当作画面可见事实。\n邻近字幕：', 'Describe visible text, objects or charts in about 70 words, as plain text without headings. Subtitles are context, not visible evidence.\nNearby subtitles: '),
 'chunk_prompt': ('整理实际提及的重点、因果关系和概念，约 200 字，直接写内容，不加标题。\n', 'Summarize only the key points, causal relationships and concepts actually mentioned, in about 90 words, as plain notes without headings.\n'),
 'merge_prompt': ('合并有依据的笔记，保留主要论点和概念，约 250 字。\n', 'Merge these evidence-based notes, preserving the main arguments and concepts, in about 90 words.\n'),
 'final_prompt': ('用简体中文 Markdown 输出「摘要」「重点」「概念解释」。摘要一段，重点最多四项，概念最多三个，总长约 450 字。画面中可核对的拼字优先于转录；不可推测未说明的字幕与画面关系。\n', 'Write English Markdown with headings "Summary", "Key points" and "Concepts explained". Use one summary paragraph, at most four key points and three concepts, about 220 words total. Prefer verified visual spelling over transcription. Do not infer unexplained subtitle/image relationships.\n'),
 'source_context': ('来源核对资料：', 'Source spelling evidence: '),
 'translate_prompt': ('忠实转换以下文字，保留结构和专有名词，不新增事实，不添加时间戳。\n', 'Translate the following text faithfully into English, preserving Markdown and proper names. Add no facts or timestamps.\n'),
 'required_language': ('必须使用简体中文回答，包括标题和解释。即使素材是英文，也要用简体中文归纳；专有名称可保留原文。', 'Required output language: English. All explanatory prose and headings must be English, even when the source is Chinese. Preserve original proper names.'),
 'error_generic': ('任务失败。请检查网络、本机模型和文件权限后重试。详细原因记录于 logs/app-errors.log。', 'The task failed. Check your network, local model and file permissions, then retry. Details are in logs/app-errors.log.'),
 'error_model': ('本机摘要模型未就绪或无法连接。请完成首次配置并检查 Ollama。详细原因记录于 logs/app-errors.log。', 'The local summary model is unavailable. Complete first-time setup and check Ollama. Details are in logs/app-errors.log.'),
 'error_whisper': ('Whisper small 未就绪或下载失败。请运行 prepare-whisper.bat；无法连接时可复制 models/whisper。切换 CPU 不会修复模型下载。详细原因记录于 logs/app-errors.log。', 'Whisper small is not ready or its download failed. Run prepare-whisper.bat or copy models/whisper. Switching to CPU cannot fix a model download. Details are in logs/app-errors.log.'),
 'error_url': ('请输入可合法访问的 HTTPS Bilibili、b23.tv 或 YouTube 链接。', 'Enter a legally accessible HTTPS Bilibili, b23.tv or YouTube URL.'),
 'error_no_media': ('视频平台这次没有提供可下载的音频或视频。B 站有时会暂时限制未登录的访问，请过一段时间再试；仍然失败时，双击软件文件夹里的 update-ytdlp.bat 更新下载组件，重启电脑后再试。本工具不会登录或绕过平台限制。详细原因记录于 logs/app-errors.log。', 'The platform did not offer any downloadable audio or video this time. Bilibili sometimes temporarily limits access without login, so try again later. If it keeps failing, double-click update-ytdlp.bat in the application folder to update the download component, restart the computer and try again. This tool does not log in or bypass platform limits. Details are in logs/app-errors.log.'),
 'error_platform': ('无法从视频平台读取这个视频。平台可能已经改版：请双击软件文件夹里的 update-ytdlp.bat 更新下载组件，重启电脑后再试。需要登录、付费或已删除的视频无法处理。详细原因记录于 logs/app-errors.log。', 'Could not read this video from the platform. The platform may have changed: double-click update-ytdlp.bat in the application folder to update the download component, restart the computer and try again. Videos that need login or payment, or were removed, cannot be processed. Details are in logs/app-errors.log.'),
}

def validate_language(language):
    if language not in LANGUAGES:
        raise ValueError('Unsupported language: ' + str(language))
    return language

@lru_cache(maxsize=3)
def converter(language):
    validate_language(language)
    return None if language == 'en' else OpenCC('t2s' if language == 'zh-CN' else 's2twp')

def normalize(text, language=DEFAULT_LANGUAGE):
    cc = converter(language)
    return cc.convert(text) if cc else text

def tr(locale, key, **values):
    validate_language(locale)
    cn, en = TEXT[key]
    template = en if locale == 'en' else normalize(cn, locale)
    if locale == 'zh-TW' and key in ('final_prompt', 'required_language'):
        template = template.replace('簡體中文', '繁體中文')
    return template.format(**values)

def friendly_error(error, language):
    text = str(error)
    if any(text == tr(code, 'busy') for code in LANGUAGES):
        return tr(language, 'busy')
    if type(error).__name__ == 'NoMediaError':
        return tr(language, 'error_no_media')
    if type(error).__name__ == 'ModelUnavailableError':
        return tr(language, 'error_whisper')
    if isinstance(error, ValueError) and ('HTTPS' in text or 'Bilibili' in text):
        return tr(language, 'error_url')
    if 'Ollama' in text or '下载本机模型' in text or '11435' in text:
        return tr(language, 'error_model')
    if type(error).__module__.startswith('yt_dlp'):
        return tr(language, 'error_platform')
    return tr(language, 'error_generic')
