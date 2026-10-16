# VideoSummarizer

简体中文 | [English](README.en.md)

Windows 免费本机视频摘要工具：Bilibili / b23.tv / YouTube、字幕优先、可选画面分析。语音识别和摘要都在本机运行，不使用付费 API 或 Ollama cloud。

## v0.3.10：首次配置可选择简体中文、繁體中文或 English

建议下载 [v0.3.10 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.10/VideoSummarizer-v0.3.10-windows-x64-with-whisper-ollama.zip)，完整解压到新的可写入文件夹。停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。页面标题下会显示 `VideoSummarizer · 当前运行版本：v0.3.10`。

首次配置窗口新增语言选择：简体中文（默认）、繁體中文或 English，切换后窗口文字马上改变。选择会保存为网页语言；之后的配置进度、网络检查、GPU 加速、yt-dlp 更新、Whisper 下载和启动提示也都使用这个语言，在网页上改语言后同样跟着变。以前这些提示只有简体中文。

另外新增英文版说明 [README.en.md](README.en.md)。

保留 v0.3.9 的全部依赖锁定与哈希校验、v0.3.8 的 B 站暂时拿不到视频时的明确提示与报告格式整理、v0.3.7 的 `update-ytdlp.bat` 与 GPU 加速提示、v0.3.6 的分享文字链接识别、v0.3.5 的网络检查（`check-network.bat`）与断点续传，以及 CPU int8 默认设置、首次配置跳过 CUDA 和独立 `install-gpu.bat`。内含 Whisper + Ollama 版仍需首次同意后联网下载其他 Python 依赖、Node.js 与 Qwen 摘要模型，不是完全离线包。升级方法见下方「升级」。

以下是当前版本的使用说明。各版本发布时的说明集中在文末「历史版本说明」，只适用于当时的版本。

## 下载与安装

### Windows 便携版（推荐）

[Releases](https://github.com/leto0309/VideoSummarizer/releases) 提供三种 Windows x64 便携版，都内置 Python 3.11，不需要预先安装 Python：

| 安装包 | 大小（约） | 已包含 |
|---|---|---|
| `windows-x64-with-whisper-ollama.zip`（推荐） | 1.97 GB | Python、Whisper small 语音模型、官方 Ollama 程序 |
| `windows-x64-with-whisper.zip` | 500 MB | Python、Whisper small 语音模型 |
| `windows-x64.zip` | 49 MB | Python |

三种都不是完全离线包。首次启动时会询问是否同意下载其余 Python 依赖（含 FFmpeg）、Node.js、包内没有的 Ollama 程序或 Whisper 模型，以及 Qwen 摘要模型，合计可能数 GB；请至少预留 15 GB 磁盘空间。开始下载前，进度窗口会先列出各下载网站能否连接；网络不稳定时，可先双击 `check-network.bat` 检查。

1. 下载 ZIP；需要时用发布页的 `*_SHA256SUMS.txt` 核对 SHA256。完整解压到有写入权限的新文件夹，不要直接在 ZIP 里运行。
2. 双击 `VideoSummarizer.exe`。首次配置窗口可以选择语言（简体中文 / 繁體中文 / English，默认简体中文），同意后在进度窗口自动配置。选择的语言也用于网页，之后的 GPU 加速、yt-dlp 更新等窗口和提示也会跟着它；在网页上改语言后同样适用。Python 依赖安装显示进度，设 45 分钟整体时限，可点「取消配置」；取消或失败会保留已有模型和摘要，重新打开即可重试。
3. 配置完成后自动打开 <http://127.0.0.1:8501/>。之后再双击同一个 EXE，会启动或重用这个文件夹的后台服务；关闭网页或进度窗口不会停止后台服务。

便携版不修改系统 PATH、不注册系统 Python、不需要管理员权限。首次配置默认跳过可选的 CUDA 运行库，语音识别使用 CPU int8。日志在 `logs/`，安装日志为 `logs/install.log` 和 `logs/desktop.log`。

### 可选：Whisper GPU 加速

网页会根据电脑情况显示提示：检测到 NVIDIA 显卡、但还没安装 GPU 加速时，会建议运行 `install-gpu.bat`。

需要 NVIDIA GPU 加速语音识别时，在首次配置完成、且没有摘要任务运行时，双击 `install-gpu.bat` 并同意下载（超过 1 GB）。窗口显示下载进度，设 20 分钟整体时限，可以取消；失败、超时或取消都不影响 CPU 模式，也不删除模型和摘要。

安装完成后重启程序，「语音识别运算」会默认使用「自动：CUDA → CPU」（没有安装时默认「只用 CPU int8」）。安装成功不代表显卡一定兼容；实际转录失败时会自动回退 CPU。RTX 50 系列等较新显卡尚未实际验证。Ollama 是否使用 GPU 由 Ollama 自行检测，与这个设置无关。

### 升级

1. 把新版完整解压到**新的**文件夹。不要覆盖旧文件夹，也不要把新版文件零散复制进旧文件夹。
2. 关闭旧版服务或重启 Windows。两个版本共用 `8501` / `11435` 端口，不能同时运行。
3. 需要保留模型和历史摘要时，复制完整的 `models` 和 `outputs` 文件夹。不要复制 `portable-ready.json`、`logs`、`PORTABLE_BUILD.json`、`runtime`、`.venv` 或旧版补丁文件。
4. 用过 Chrome 书签时，先在旧文件夹运行 `remove-bookmark.bat`，再在新文件夹运行 `install-bookmark.bat`；已注册到旧文件夹的连接不会被自动覆盖。
5. 打开新版后，确认页面标题下的「当前运行版本」。它显示的是后台实际运行的版本；如果仍是旧版本，说明旧版服务还在运行。

### 开发者：源码版（需要 Python 3.11）

1. 下载 Releases 中的 `source.zip`，解压到有写入权限的文件夹。
2. 从 [Python 官方网站](https://www.python.org/downloads/windows/) 安装 64 位 Python 3.11。
3. 双击 `setup.bat` 并同意项目内下载。它会创建 `.venv`，安装 Python 依赖，下载 Node.js、Ollama、默认 Qwen 摘要模型和 Whisper small，并运行诊断；不会安装 CUDA 运行库。
4. 双击 `start.bat`，等待启动成功后打开 <http://127.0.0.1:8501/>，保持启动窗口开启。
5. 需要 GPU 加速时，同样使用 `install-gpu.bat`。

在便携版文件夹里运行 `setup.bat`、`start.bat` 或 `install-gpu.bat`，会直接转交给 `VideoSummarizer.exe`。安装器不安装系统 CUDA Toolkit，不修改全局 PATH。

## 环境与模型

- 目标系统：Windows 10 22H2 / Windows 11 x64。其他系统未验证。
- 建议 16 GB 内存，并预留至少 15 GB 磁盘空间；这是建议配置，不是验证过的最低需求。
- 语音识别：Whisper `small`，默认 CPU `int8`；安装 GPU 加速并选择「自动」后，兼容的 NVIDIA GPU 使用 CUDA `int8_float16`，失败回退 CPU。CPU 处理长视频可能较慢。
- Whisper small 约 464 MiB，内含 Whisper 的安装包已附带；其他情况从 Hugging Face 官方仓库下载到 `models/whisper`。本机已有完整模型时直接使用，转录时不再联网检查。
- 摘要模型：Ollama `qwen3-vl:4b-instruct`；未检测到 NVIDIA GPU，或显存少于 6000 MiB 时使用 `qwen3-vl:2b-instruct`。推理速度取决于硬件。
- 上下文 4096 tokens，长字幕分段摘要后再合并。Whisper 和 Ollama 依次运行，同一时间只处理一个摘要任务。
- 本机端点：网页 `127.0.0.1:8501`，项目 Ollama `127.0.0.1:11435`，都不对外开放。

自动测试验证程序逻辑；发布流程还会在解压后的 Windows 包里运行测试、启动器自检，并离线加载 Whisper。它们都不执行摘要模型推理或平台视频下载。早期版本曾在一台 RTX 3050 Laptop（4 GB 显存）/ 16 GB 内存的 Windows 电脑上验证完整视频流程（字幕、CUDA / CPU 转录与画面时间戳），这不代表所有设备或每个视频都可用。

## 摘要、产出与清理

先读取人工字幕，其次自动字幕；确实没有字幕时才下载音频并用 Whisper 转录。可选下载低分辨率视频，用 FFmpeg 截取约 8 张均匀分布的画面，时间取自实际解码画面的 PTS。

成功的产出保存在 `outputs/日期时间_任务ID/`：

- `summary.md`：视频信息、摘要、重点、概念解释、字幕时间轴和画面描述。
- `subtitles.srt`：原始字幕或语音转录，保留来源时间以便核对。
- `metadata.json`：来源、模型、运算方式、画面 PTS、SHA256 与分析信息。
- `translations/语言代码/`：在页面上生成的其他语言版本；原始摘要和 SRT 不会被改写。

产出写入成功后，删除该任务的视频、音频和截图；失败任务的暂存保留 24 小时。项目暂存上限 5 GB，只清理带项目标记的任务目录，不删除模型或其他文件。

语音识别和摘要都可能出错，尤其是人名、专有名词和音质较差的音频。名称修正必须有来源资料支持；摘要不能代替核对原视频。画面抽样不会覆盖整个视频。

## Chrome 启动书签（可选）

1. 完成首次配置后（便携版首次启动，或源码版 `setup.bat`），双击 `install-bookmark.bat`，为当前 Windows 用户注册连接。
2. 在 Chrome 书签管理器新增书签，网址填 `videosummarizer://open`。
3. 点书签时确认打开外部应用。启动器是 Python，提示中可能显示 Python。

服务已运行时直接打开网页，未运行时在后台启动并等待就绪。冷启动可能需要约两分钟，进度记录在 `logs/bookmark.log` 和 `logs/startup.log`。Chrome 不接受协议书签时，可以收藏项目里的 `bookmark.html` 再点其中的按钮。

书签不是开机自启；关闭网页不会停止后台服务。要移除注册，运行 `remove-bookmark.bat`，模型和摘要保留。启动器使用系统默认浏览器。

## 常见问题

### 首次配置下载失败 / 检查网络

首次配置需要从几个不同的网站下载，任何一个连不上都会让配置停下：

| 网站 | 下载内容 | 已内含在哪些安装包 |
|---|---|---|
| PyPI（pypi.org、files.pythonhosted.org） | Python 依赖（含 FFmpeg）、可选 CUDA 运行库 | 无 |
| Node.js 官网（nodejs.org） | Node.js | 无 |
| GitHub | Ollama 程序 | 内含 Whisper + Ollama 版 |
| Ollama 模型库（registry.ollama.ai） | Qwen 摘要模型 | 无 |
| Hugging Face | Whisper 语音模型 | 两种内含 Whisper 版 |

1. 双击软件文件夹里的 `check-network.bat`，它会逐个测试这些网站能否连接，结果保存在 `logs/network-check.json`。只发送连接测试请求，不上传任何资料，首次配置前也能运行。便携版首次配置开始时也会自动显示同样的检查，并标出这次配置需要哪些网站。
2. 配置失败时，进度窗口最后会说明是哪个网站、影响什么，以及可以怎么做，并再检查一次该网站能否连接。完整记录保存在 `logs/desktop.log` 和 `logs/install.log`。
3. 重新打开 `VideoSummarizer.exe` 即可重试：Python 依赖会复用 `tools/pip-cache`，Node.js 和 Ollama 程序会接着已下载的部分继续，Qwen 模型由 Ollama 自行续传。
4. 连不上 GitHub 时，改用内含 Whisper + Ollama 版；连不上 Hugging Face 时，改用内含 Whisper 的安装包。
5. 连不上 Ollama 模型库时，可以在能下载的电脑完成配置，再把整个 `models/ollama` 文件夹复制到这台电脑软件文件夹的同一位置；首次配置发现本机已有模型时会跳过下载。

「可以连接」只表示能建立连接，不保证大文件一定能完整下载。

### Whisper 下载超时 / WinError 10060 / LocalEntryNotFoundError

这表示无法下载语音模型，且本机没有完整模型；不是 CUDA 计算失败，改用 CPU 也无法解决。网页能打开不代表所有模型都已下载。有字幕的视频仍可处理。

1. 网络无法连接 Hugging Face 时，最简单的方法是改用内含 Whisper 的安装包。
2. 确认能打开 [官方 small 模型页面](https://huggingface.co/Systran/faster-whisper-small)，然后在软件文件夹双击 `prepare-whisper.bat` 并同意下载。失败原因记录在 `logs/whisper-download.log`，已下载的部分保留以便重试。
3. 这台电脑无法联网时，可以在能下载的电脑完成第 2 步，关闭程序后把**整个 `models/whisper` 文件夹**复制到这台电脑软件文件夹的同一位置。源缓存使用符号链接时，请复制实际文件内容。
4. 也可以从官方模型页面下载 `model.bin`、`config.json`、`tokenizer.json`、`vocabulary.txt`（或 `vocabulary.json`），放到 `models/whisper/small/`；上游有 `preprocessor_config.json` 时一并复制。必须是 faster-whisper 的 CTranslate2 模型，OpenAI 原始 `.pt` 文件不能直接使用。
5. 再运行 `prepare-whisper.bat`。本机文件完整时直接通过检查，不联网下载；页面的「Whisper 语音模型状态」也会显示是否就绪。

### 其他问题

- **第一次启动没有反应**：留意浏览器的「打开外部应用 / Python」提示；Ollama 初始化期间查看 `logs/startup.log`。
- **端口已被占用**：确认是否还有本项目的其他文件夹或其他程序在运行。未知的 Ollama 服务会被拒绝使用，程序不会结束其他程序的进程。
- **CUDA 失败**：转录会自动回退 CPU。需要诊断信息时，在软件文件夹运行 `runtime\python.exe diagnostics.py`（便携版）或 `.venv\Scripts\python.exe diagnostics.py`（源码版），结果也保存在 `logs/diagnostics.json`。提交问题前删除私人资料和本机路径。
- **平台下载失败**：B 站、YouTube 改版后，下载组件 yt-dlp 可能需要更新。双击软件文件夹里的 `update-ytdlp.bat`，选择「更新」从 PyPI 安装最新版本（只装在本软件文件夹里），重启电脑后再试；更新后反而出问题时，再运行它选择「恢复」，装回本版本测试过的版本。当前版本显示在网页的「关于 VideoSummarizer」里。摘要任务运行中不能更新。遇到登录、付费、验证或其他限制时，工具会停止，不会绕过。
- **提示「视频平台这次没有提供可下载的音频或视频」**：B 站有时会暂时限制未登录的访问，这时同一个视频也拿不到音频或视频；请过一段时间（几分钟到几小时）再试。短时间内反复重试可能让限制持续更久。仍然失败时，再用上一条的 `update-ytdlp.bat` 更新下载组件。本工具不读取浏览器 cookies，也不会登录或绕过平台限制。
- **提示「下载中途连接中断或超时」**：这是网络暂时不稳定，不是平台改版。下载会自动重试 10 次，每次稍等片刻，并从已下载的部分接着下；仍然失败时，稍后再点一次「开始生成摘要」即可，不需要更新下载组件。
- **升级后仍是旧版本**：见上方「升级」，先关闭旧版服务再从新文件夹启动。

## 开发与贡献

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.lock
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

测试不需要下载 AI 模型。安装和实际推理需要另外验证，请参考 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 使用范围与隐私

只处理你有权合法访问的内容。不读取浏览器 cookies，不使用账号密码，不绕过 DRM、付费、登录、验证或地区限制。下载器只接受 HTTPS 的 Bilibili / b23.tv / YouTube 链接。

Ollama cloud 已禁用；字幕和画面只发送到项目自己的本机 Ollama。视频平台、GitHub、PyPI、Node.js、Ollama 模型库和 Hugging Face 仍会收到必要的下载请求。程序和模型的首次下载都需要你同意。

项目代码使用 [MIT](LICENSE) 许可。第三方程序、套件和模型保留各自的许可，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。源码 ZIP 不含第三方二进制文件或模型权重；Windows 便携包另含 CPython 及其上游许可，内含 Whisper / Ollama 的版本另含对应的模型或程序及其许可，均不含下载的视频。

## 历史版本说明

以下是各版本发布时的说明，原文保留作为记录，只适用于当时的版本。其中「自动安装 CUDA」「下载 source.zip 覆盖旧目录」等做法已不再适用；当前步骤以上方说明为准。

### v0.3.9：首次配置装到的每个包都经过测试和校验

建议下载 [v0.3.9 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.9/VideoSummarizer-v0.3.9-windows-x64-with-whisper-ollama.zip)，完整解压到新的可写入文件夹。停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。页面标题下会显示 `VideoSummarizer · 当前运行版本：v0.3.9`。

首次配置会从 PyPI 下载 Python 依赖。以前只固定了 9 个直接依赖的版本，它们带进来的其他包会装当天的最新版，上游一改版就可能装不上。现在全部 61 个包都固定在测试过的版本，并核对每个文件的 SHA256，对不上就拒绝安装；可选 GPU 加速的 3 个包也一样。

`update-ytdlp.bat` 完成后会写明是「已更新」还是「已恢复」；「恢复」会把 yt-dlp 和被更新改动过的依赖一起装回测试过的版本。

保留 v0.3.8 的 B 站暂时拿不到视频时的明确提示与报告格式整理、v0.3.7 的 `update-ytdlp.bat` 与 GPU 加速提示、v0.3.6 的分享文字链接识别、v0.3.5 的网络检查（`check-network.bat`）与断点续传，以及 CPU int8 默认设置、首次配置跳过 CUDA 和独立 `install-gpu.bat`。内含 Whisper + Ollama 版仍需首次同意后联网下载其他 Python 依赖、Node.js 与 Qwen 摘要模型，不是完全离线包。升级方法见下方「升级」。

### v0.3.8：B 站暂时拿不到视频时给出明确提示

建议下载 [v0.3.8 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.8/VideoSummarizer-v0.3.8-windows-x64-with-whisper-ollama.zip)，完整解压到新的可写入文件夹。停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。页面标题下会显示 `VideoSummarizer · 当前运行版本：v0.3.8`。

B 站有时会暂时限制未登录的访问，这时同一个视频也拿不到音频或视频。以前页面只显示「请检查网络、本机模型和文件权限」，容易查错方向；现在会明确提示「视频平台这次没有提供可下载的音频或视频」，并说明请过一段时间再试，仍然失败时用 `update-ytdlp.bat` 更新下载组件。本工具不会登录或绕过平台限制。详见下方「常见问题」。

摘要报告的格式也更整齐：本机模型在画面描述或时间线小节里自己加的大标题（例如「# 画面描述」）会去掉或改为粗体，不再打乱报告的标题层级；`metadata.json` 仍保存模型原文，方便核对。

保留 v0.3.7 的 `update-ytdlp.bat` 与 GPU 加速提示、v0.3.6 的分享文字链接识别、v0.3.5 的网络检查（`check-network.bat`）与断点续传，以及 CPU int8 默认设置、首次配置跳过 CUDA 和独立 `install-gpu.bat`。内含 Whisper + Ollama 版仍需首次同意后联网下载其他 Python 依赖、Node.js 与 Qwen 摘要模型，不是完全离线包。升级方法见下方「升级」。

### v0.3.7：可自行更新 yt-dlp，网页提示 GPU 加速

建议下载 [v0.3.7 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.7/VideoSummarizer-v0.3.7-windows-x64-with-whisper-ollama.zip)，完整解压到新的可写入文件夹。停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。页面标题下会显示 `VideoSummarizer · 当前运行版本：v0.3.7`。

B 站、YouTube 改版导致下载失败时，可以双击软件文件夹里的 `update-ytdlp.bat` 更新下载组件 yt-dlp，不必等新版本；更新后出问题，再运行它选择「恢复」即可装回本版本测试过的版本。详见下方「常见问题」。网页的「关于 VideoSummarizer」会显示当前 yt-dlp 版本。

网页会根据电脑情况提示 GPU 加速：检测到 NVIDIA 显卡、但还没安装 GPU 加速时，建议运行 `install-gpu.bat`；安装后「语音识别运算」默认改为「自动：CUDA → CPU」。

其他改进：程序提示统一为简体中文；摘要记录里的来源链接去掉 `vd_source`、`si` 等分享跟踪参数；摘要中的 16:9、3:1 等比例和比分不再被误当成时间戳清除；日志超过 2 MB 自动轮转，只保留一份旧档；CPU 语音识别按电脑核心数使用线程（最多 8 个）。

保留 v0.3.6 的分享文字链接识别、v0.3.5 的网络检查（`check-network.bat`）与断点续传，以及 CPU int8 默认设置、首次配置跳过 CUDA 和独立 `install-gpu.bat`。内含 Whisper + Ollama 版仍需首次同意后联网下载其他 Python 依赖、Node.js 与 Qwen 摘要模型，不是完全离线包。升级方法见下方「升级」。

### v0.3.6：链接栏可直接粘贴分享文字

建议下载 [v0.3.6 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.6/VideoSummarizer-v0.3.6-windows-x64-with-whisper-ollama.zip)，完整解压到新的可写入文件夹。停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。页面标题下会显示 `VideoSummarizer · 当前运行版本：v0.3.6`。

链接栏现在可以直接粘贴 Bilibili 或 YouTube「分享」复制的整段文字，例如 `【视频标题】 https://www.bilibili.com/video/...`。程序会取出其中第一个 `https://` 链接，并在输入框下方显示将使用的链接；只接受 HTTPS 的 Bilibili、b23.tv 和 YouTube，规则没有放宽。摘要和记录文件只保存链接，不保存粘贴的标题。

处理失败时，错误提示改为显示在「处理停止」状态框下方，不会再随状态框收起而看不到；详细原因仍记录在 `logs/app-errors.log`。

保留 v0.3.5 的网络检查（`check-network.bat`）、Node.js / Ollama 程序断点续传，以及 v0.3.2 起的 CPU int8 默认设置、首次配置跳过 CUDA 和独立 `install-gpu.bat`。内含 Whisper + Ollama 版仍需首次同意后联网下载其他 Python 依赖、Node.js 与 Qwen 摘要模型，不是完全离线包。升级方法见下方「升级」。

### v0.3.5：首次配置先检查下载网站，下载中断可续传

建议下载 [v0.3.5 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.5/VideoSummarizer-v0.3.5-windows-x64-with-whisper-ollama.zip)，完整解压到新的可写入文件夹。停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。页面标题下会显示 `VideoSummarizer · 当前运行版本：v0.3.5`。

首次配置开始前，进度窗口会先检查 PyPI、Node.js 官网、GitHub、Ollama 模型库和 Hugging Face 能否连接，并标出这次配置需要哪些网站。也可以随时双击 `check-network.bat` 检查，结果保存在 `logs/network-check.json`；检查只发送连接测试请求，不上传资料。下载失败时，进度窗口最后会说明是哪个网站、影响什么，以及可以怎么做。

Node.js 和 Ollama 程序下载中断后会自动重试，并接着已下载的部分继续，最后仍校验官方 SHA256。本机已有 Qwen 摘要模型时不再重新下载，因此可以从另一台电脑复制完整的 `models/ollama` 文件夹。这些改进没有在中国大陆网络实测；「可以连接」不代表大文件一定能下载完成。

保留 v0.3.2 起的 CPU int8 默认设置、首次配置跳过 CUDA 和独立 `install-gpu.bat`。内含 Whisper + Ollama 版仍需首次同意后联网下载其他 Python 依赖、Node.js 与 Qwen 摘要模型，不是完全离线包。升级方法见下方「升级」。

### v0.3.4：修正内含 Whisper 安装包的来源记录

建议下载 [v0.3.4 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.4/VideoSummarizer-v0.3.4-windows-x64-with-whisper-ollama.zip)，完整解压到新的可写入文件夹。停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。页面标题下会显示 `VideoSummarizer · 当前运行版本：v0.3.4`。

v0.3.4 是维护版本，程序功能与 v0.3.3 相同。内含 Whisper 的两种安装包中，`WHISPER_BUNDLE.json` 的 `base_sha256` 现在记录实际使用的标准便携包 SHA256；v0.3.3 及更早版本误记为 `vocabulary.txt` 的哈希。标准便携包和 Whisper 模型文件一直逐一校验，这个错误只影响来源记录，不影响运行。v0.3.3 运行正常的用户不必为此升级。

保留 v0.3.2 起的 CPU int8 默认设置、首次配置跳过 CUDA 和独立 `install-gpu.bat`。内含 Whisper + Ollama 版仍需首次同意后联网下载其他 Python 依赖、Node.js 与 Qwen 摘要模型，不是完全离线包。升级方法见下方「升级」。

### v0.3.3：页面显示当前运行版本

建议下载 [v0.3.3 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.3/VideoSummarizer-v0.3.3-windows-x64-with-whisper-ollama.zip)，完整解压到新的可写入文件夹。停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。

页面标题下固定显示 `VideoSummarizer · 当前运行版本：v0.3.3`。“关于 VideoSummarizer”显示安装包类型，并提供该版本的更新说明链接；这些标签随页面切换简体中文、繁體中文或 English。版本显示无需联网、不会调用模型，也不会自动检查或安装更新。

显示的是当前后台所加载代码的版本。下载新版 ZIP 后，如果书签仍连接旧版后台，页面不会因此变成新版。请关闭旧版服务，再从新版文件夹启动。若安装包记录与代码版本不一致，页面保留运行代码的版本、显示未知安装包类型并提示完整解压；不要把新版文件零散覆盖到旧文件夹。

保留 v0.3.2 的 CPU int8 默认设置、首次配置跳过 CUDA 和独立 `install-gpu.bat`。内含 Python、Whisper small 和完整官方 Ollama；其余 Python 依赖、Node.js 与 Qwen 摘要模型仍需首次同意后联网下载。本包不是完全离线包。原有模型与产出可自行复制完整的 `models` 和 `outputs` 文件夹；不要复制旧版就绪标记、日志、补丁或 `PORTABLE_BUILD.json`。

### v0.3.2：首次配置不再等待 CUDA 下载

建议下载 [v0.3.2 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.2/VideoSummarizer-v0.3.2-windows-x64-with-whisper-ollama.zip)。完整解压到新的可写入文件夹，停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。不需要预装 Python，也不需要 v0.3.1 的临时启动补丁。

首次配置默认跳过可选 CUDA Python 库，网页默认选择 CPU int8 语音转录；解决大文件 CUDA 下载阻塞整个首次启动的问题。CPU 转录通常较慢；Ollama 的 GPU 使用仍由 Ollama 自行检测，不受 Whisper 运算模式影响。其他依赖、Node.js 和 Qwen 摘要模型仍需联网下载，本版不是完全离线包。

需要 NVIDIA GPU 加速时，在首次配置完成、当前摘要任务结束后，双击 `install-gpu.bat` 并同意下载。GPU 安装窗口显示下载字节数和百分比，限制重试次数，并设 **20 分钟整体时限**；失败、超时或取消不清除模型、摘要和 CPU 就绪状态。安装完成后，在摘要任务结束时重启程序，网页改选「自动：CUDA → CPU」。GPU 是否兼容仍需真实转录验证，不保证所有显卡或驱动均可使用。

首次配置的 Python 依赖安装也显示持续进度，每次设 **45 分钟整体时限**。Windows 配置窗口新增「取消配置」按钮；确认取消后只停止本次安装子进程树，保留现有模型和摘要，可重新打开软件重试。Node/Ollama 程序下载与模型下载仍按各自网络超时处理，这些步骤没有统一的 45 分钟总时限。日志保留在 `logs/install.log` 与 `logs/desktop.log`。本地 pip 下载缓存存放于 `tools/pip-cache`，仅复用已经缓存的数据，不承诺所有部分下载均可跨次续传。

保留简体中文默认设置，以及页面和摘要独立切换简体中文、繁體中文和 English 的功能。升级使用新文件夹，不覆盖旧版；模型和历史产出可自行复制完整的 `models` 与 `outputs` 文件夹。不要复制旧版 `portable-ready.json`、补丁文件或 `skip-cuda-install.flag`。

### v0.3.1：内置 Ollama 的 Windows 下载

建议下载 [v0.3.1 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.1/VideoSummarizer-v0.3.1-windows-x64-with-whisper-ollama.zip)。包含 Python、Whisper small 和完整官方 Ollama 0.40.2 Windows x64 程序及运行库；首次配置直接使用包内 Ollama，解决安装时下载 Ollama ZIP 连接中断的问题。解压到新文件夹，停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。请至少预留 15 GB 空间，保留 `tools/ollama` 下全部文件。

这仍不是完全离线包：其他 Python 依赖、FFmpeg、Node.js、可选 CUDA wheel 和 Qwen 摘要模型仍在首次同意后下载，其他服务器的网络问题仍可能影响配置。标准 Windows / 仅含 Whisper 版保留供需要较小下载的用户选择。

保留 v0.3.0 的简体中文默认设置，以及页面和摘要独立切换简体中文、繁體中文和 English 的功能。原始摘要、SRT 和可核对时间戳不因语言转换而改写。

内置 Ollama 原版 ZIP 固定 SHA256 `e29ad1d5063dd4b54b2492d9b00adab2cff9621bfa654b6c92aa8d6f1fdfe7fc`，与官方发布清单一致；保留原始运行库、组件许可和额外 Ollama MIT 许可。包内 `OLLAMA_BUNDLE.json` 记录来源、版本和逐文件哈希，发布页提供 `WITH_WHISPER_OLLAMA_SHA256SUMS.txt`。

### v0.3.0：默认简体中文，页面和摘要三语切换

**v0.3.0：默认简体中文，页面和摘要支持「简体中文 / 繁體中文 / English」分别选择。** 页面立即切换，输入链接、模型和 CPU/GPU 设置会保留；语言偏好保存在软件文件夹的 `language-settings.json`。摘要默认跟随页面，也可单独指定。页面切换不会自动调用模型或改写已有摘要。

建议下载 [v0.3.0 Windows 内含 Whisper 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.0/VideoSummarizer-v0.3.0-windows-x64-with-whisper.zip)，完整解压后双击 `VideoSummarizer.exe`。包含 Python 和 Whisper small；首次仍需同意下载其他依赖、Ollama 和摘要模型。较小的 [标准 Windows 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.0/VideoSummarizer-v0.3.0-windows-x64.zip)不包含 Whisper 模型。旧版下载保留在 Releases 历史记录。

已有摘要可点击「生成所选语言版本」。简繁转换通常无需模型；涉及英文或旧版没有独立摘要正文的输出，需要本机模型处理。原版与原始 SRT 保留，其他语言存放在任务的 `translations/语言代码/` 中，包含独立的 `summary.md` 与 `metadata.json`；生成过的版本可立即切换。来源标题、作者、网址、截图 SHA256 和精确时间戳保留原文。摘要仍可能有理解、翻译或专有名词错误，请核对原视频。浏览器、Windows 和 Streamlit 内置菜单不属于应用文字表；第三方原始错误写入日志，页面展示所选语言的处理建议。

升级请解压到新的可写入文件夹，不覆盖旧版；正常关闭旧版服务或重启 Windows 后再启动新版，避免共用端口冲突。可自行复制旧版 `outputs` 与完整的 `models` 文件夹。不会自动改写旧摘要或迁移系统设置。

### v0.2.1 及更早版本（原文为繁体中文）

**v0.2.1 提供 Windows x64 便攜版，內置 Python 3.11.17，無需預先安裝 Python。** 解壓後雙擊 `VideoSummarizer.exe`。首次使用仍需同意自動下載影片/語音依賴、Ollama、Node.js 和模型；完成後直接啟動本機網頁。沒有付費 API，不使用 Ollama cloud。

#### 一般使用者：免預裝 Python 的 Windows 便攜版

**無法連線 Hugging Face 的使用者可直接下載 [v0.2.1 內含 Whisper 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.2.1/VideoSummarizer-v0.2.1-windows-x64-with-whisper.zip)**（約 500 MB）。這是一個新資料夾使用的完整 Windows 安裝包：包含相同的 Python / EXE 和已驗證的 small 語音模型，解壓後雙擊 `VideoSummarizer.exe`，不用覆盖舊版或另行搬移語音模型。首次仍需同意自動下載其他依賴、Ollama 和摘要模型，這不是全部依賴預裝的完全離線包。若舊版仍在背景運行，先停止舊版專案服務或重啟 Windows，再開啟新資料夾；兩份不能同時占用相同服務埠。

下列標準便攜版約 47 MB，沒有內含語音模型：

1. 從 [Releases](https://github.com/leto0309/VideoSummarizer/releases) 下載 **VideoSummarizer-v0.2.1-windows-x64.zip**，完整解壓到有寫入權限的本機資料夾，勿直接在 ZIP 內執行。
2. 雙擊 **VideoSummarizer.exe**。首次會詢問是否允許下載免費依賴和模型；同意後在進度視窗自動配置，無需手動安裝 Python 或輸入 pip 指令。取消時不下載。
3. 配置成功後自動開啟瀏覽器。之後雙擊同一 EXE 即可啟動或重用此資料夾的背景服務。
4. 可選執行 `install-bookmark.bat` 安裝目前使用者的啟動書籤；需先完成首次配置。

便攜包內置完整 CPython、原生 .NET Framework 啟動器和預製 srt wheel；其餘 Python 套件、FFmpeg、Ollama、Node.js、CUDA 執行庫和模型於首次同意後下載到軟體資料夾。依賴採 wheel 安裝，首次配置不需編譯器。這不是完全離線包。目標 Windows 10 22H2 / Windows 11 x64（系統內建 .NET Framework 4.8）；不註冊系統 Python、不改全域 PATH、不需要管理員權限。使用 Astral python-build-standalone 20261009 的 CPython 3.11.17，構建時核對固定 SHA256。

進度視窗顯示配置與錯誤，進行中請保持開啟。成功後可關閉進度視窗，背景服務仍會運行；日誌保留在 `logs/`。首次配置嘗試預先下載 Whisper small；若 Hugging Face 無法連線，會顯示警告，仍允許處理有字幕的影片。無字幕影片需要先完成語音模型。可雙擊 `prepare-whisper.bat` 重試；既有摘要與模型保留。兩份資料夾仍共用固定服務埠，請勿同時啟動；未知服務不會被接管或關閉。

便攜版自動測試在解壓的發布 ZIP 中，直接以 EXE 啟動內置 Python，並移除 PATH 中的 Python 位置；檢查首次配置判斷、依賴安裝、單元測試、FFmpeg、Whisper 匯入、網頁載入及實際 HTTP 健康端點。此測試不下載模型、不驗證所有 GPU，也未自動操作桌面進度視窗。

#### 開發者：原始碼版（仍需 Python）

1. 從 [Releases](https://github.com/leto0309/VideoSummarizer/releases) 下載原始碼 ZIP，解壓到你有寫入權限的本機資料夾，例如 `D:\VideoSummarizer`。首次發布前也可使用 GitHub 的 Code → Download ZIP。
2. 從 [Python 官方網站](https://www.python.org/downloads/windows/) 安裝 **Python 3.11、Windows 64 位**。保留 Python Launcher，或讓 `python` 指令指向 Python 3.11。
3. 雙擊 `setup.bat`，確認允許專案內下載。安裝器建立 `.venv`，下載 Ollama / Node.js、Python 依賴和預設模型；視網速可能需要較長時間與數 GB 流量。
4. 雙擊 `start.bat`，等待提示啟動成功，再開啟 <http://127.0.0.1:8501/>。請保持啟動視窗開啟。
5. 貼上影片連結，確認你有權處理內容，按「開始產生摘要」。

安裝器不安裝系統 CUDA Toolkit，不修改全域 PATH。FFmpeg 由 imageio-ffmpeg 套件提供。可選 CUDA 執行庫安裝失敗時，Whisper 回退 CPU；模型下載失敗會停止並顯示錯誤，重新執行 setup.bat 可重試。

首版固定 Ollama 0.40.2、Node.js 24.19.0 和 requirements.txt 的直接依賴版本；官方 ZIP 下載會驗證 SHA256。傳遞依賴與模型標籤由上游提供，未宣稱整個安裝環境逐位元可重現。

#### v0.2.0 升級到 v0.2.1（僅適用於當時版本）

v0.2.0 使用者可下載 v0.2.1 **source.zip**，將其中 `VideoSummarizer` 資料夾內的程式檔覆蓋到既有軟體目錄。便攜版保留原有 `VideoSummarizer.exe`、`runtime`、`tools`、`models`、`outputs` 與 `portable-ready.json`，不需要重裝 Python 或 Ollama。完成後執行 `prepare-whisper.bat`；關閉原來的網頁並重新開啟以載入新版。自訂修改過的原始碼請先備份。修正網路錯誤提示不能保證 Hugging Face 在每個網路環境都可連線。
