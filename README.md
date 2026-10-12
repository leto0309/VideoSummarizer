# VideoSummarizer

## v0.3.4：修正内含 Whisper 安装包的来源记录

建议下载 [v0.3.4 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.4/VideoSummarizer-v0.3.4-windows-x64-with-whisper-ollama.zip)，完整解压到新的可写入文件夹。停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。页面标题下会显示 `VideoSummarizer · 当前运行版本：v0.3.4`。

v0.3.4 是维护版本，程序功能与 v0.3.3 相同。内含 Whisper 的两种安装包中，`WHISPER_BUNDLE.json` 的 `base_sha256` 现在记录实际使用的标准便携包 SHA256；v0.3.3 及更早版本误记为 `vocabulary.txt` 的哈希。标准便携包和 Whisper 模型文件一直逐一校验，这个错误只影响来源记录，不影响运行。v0.3.3 运行正常的用户不必为此升级。

保留 v0.3.2 起的 CPU int8 默认设置、首次配置跳过 CUDA 和独立 `install-gpu.bat`。内含 Whisper + Ollama 版仍需首次同意后联网下载其他 Python 依赖、Node.js 与 Qwen 摘要模型，不是完全离线包。升级方法与 v0.3.3 相同：使用新文件夹，可复制完整的 `models` 和 `outputs`，不要复制旧版就绪标记、日志、补丁或 `PORTABLE_BUILD.json`。

以下保留此前版本的说明。

## v0.3.3：页面显示当前运行版本

建议下载 [v0.3.3 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.3/VideoSummarizer-v0.3.3-windows-x64-with-whisper-ollama.zip)，完整解压到新的可写入文件夹。停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。

页面标题下固定显示 `VideoSummarizer · 当前运行版本：v0.3.3`。“关于 VideoSummarizer”显示安装包类型，并提供该版本的更新说明链接；这些标签随页面切换简体中文、繁體中文或 English。版本显示无需联网、不会调用模型，也不会自动检查或安装更新。

显示的是当前后台所加载代码的版本。下载新版 ZIP 后，如果书签仍连接旧版后台，页面不会因此变成新版。请关闭旧版服务，再从新版文件夹启动。若安装包记录与代码版本不一致，页面保留运行代码的版本、显示未知安装包类型并提示完整解压；不要把新版文件零散覆盖到旧文件夹。

保留 v0.3.2 的 CPU int8 默认设置、首次配置跳过 CUDA 和独立 `install-gpu.bat`。内含 Python、Whisper small 和完整官方 Ollama；其余 Python 依赖、Node.js 与 Qwen 摘要模型仍需首次同意后联网下载。本包不是完全离线包。原有模型与产出可自行复制完整的 `models` 和 `outputs` 文件夹；不要复制旧版就绪标记、日志、补丁或 `PORTABLE_BUILD.json`。

以下保留此前版本的说明。

## v0.3.2：首次配置不再等待 CUDA 下载

建议下载 [v0.3.2 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.2/VideoSummarizer-v0.3.2-windows-x64-with-whisper-ollama.zip)。完整解压到新的可写入文件夹，停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。不需要预装 Python，也不需要 v0.3.1 的临时启动补丁。

首次配置默认跳过可选 CUDA Python 库，网页默认选择 CPU int8 语音转录；解决大文件 CUDA 下载阻塞整个首次启动的问题。CPU 转录通常较慢；Ollama 的 GPU 使用仍由 Ollama 自行检测，不受 Whisper 运算模式影响。其他依赖、Node.js 和 Qwen 摘要模型仍需联网下载，本版不是完全离线包。

需要 NVIDIA GPU 加速时，在首次配置完成、当前摘要任务结束后，双击 `install-gpu.bat` 并同意下载。GPU 安装窗口显示下载字节数和百分比，限制重试次数，并设 **20 分钟整体时限**；失败、超时或取消不清除模型、摘要和 CPU 就绪状态。安装完成后，在摘要任务结束时重启程序，网页改选「自动：CUDA → CPU」。GPU 是否兼容仍需真实转录验证，不保证所有显卡或驱动均可使用。

首次配置的 Python 依赖安装也显示持续进度，每次设 **45 分钟整体时限**。Windows 配置窗口新增「取消配置」按钮；确认取消后只停止本次安装子进程树，保留现有模型和摘要，可重新打开软件重试。Node/Ollama 程序下载与模型下载仍按各自网络超时处理，这些步骤没有统一的 45 分钟总时限。日志保留在 `logs/install.log` 与 `logs/desktop.log`。本地 pip 下载缓存存放于 `tools/pip-cache`，仅复用已经缓存的数据，不承诺所有部分下载均可跨次续传。

保留简体中文默认设置，以及页面和摘要独立切换简体中文、繁體中文和 English 的功能。升级使用新文件夹，不覆盖旧版；模型和历史产出可自行复制完整的 `models` 与 `outputs` 文件夹。不要复制旧版 `portable-ready.json`、补丁文件或 `skip-cuda-install.flag`。

以下内容是历史版本说明；其中自动安装 CUDA 的描述仅适用于旧版。

## v0.3.1：内置 Ollama 的 Windows 下载

建议下载 [v0.3.1 内含 Whisper + Ollama 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.1/VideoSummarizer-v0.3.1-windows-x64-with-whisper-ollama.zip)。包含 Python、Whisper small 和完整官方 Ollama 0.40.2 Windows x64 程序及运行库；首次配置直接使用包内 Ollama，解决安装时下载 Ollama ZIP 连接中断的问题。解压到新文件夹，停止旧版服务或重启 Windows 后，双击 `VideoSummarizer.exe`。请至少预留 15 GB 空间，保留 `tools/ollama` 下全部文件。

这仍不是完全离线包：其他 Python 依赖、FFmpeg、Node.js、可选 CUDA wheel 和 Qwen 摘要模型仍在首次同意后下载，其他服务器的网络问题仍可能影响配置。标准 Windows / 仅含 Whisper 版保留供需要较小下载的用户选择。

保留 v0.3.0 的简体中文默认设置，以及页面和摘要独立切换简体中文、繁體中文和 English 的功能。原始摘要、SRT 和可核对时间戳不因语言转换而改写。

内置 Ollama 原版 ZIP 固定 SHA256 `e29ad1d5063dd4b54b2492d9b00adab2cff9621bfa654b6c92aa8d6f1fdfe7fc`，与官方发布清单一致；保留原始运行库、组件许可和额外 Ollama MIT 许可。包内 `OLLAMA_BUNDLE.json` 记录来源、版本和逐文件哈希，发布页提供 `WITH_WHISPER_OLLAMA_SHA256SUMS.txt`。

以下 v0.3.0 / v0.2.1 内容保留为此前版本及其他发行包说明。

Windows 免费本机视频摘要工具：Bilibili / b23.tv / YouTube、字幕优先、可选画面分析。

**v0.3.0：默认简体中文，页面和摘要支持「简体中文 / 繁體中文 / English」分别选择。** 页面立即切换，输入链接、模型和 CPU/GPU 设置会保留；语言偏好保存在软件文件夹的 `language-settings.json`。摘要默认跟随页面，也可单独指定。页面切换不会自动调用模型或改写已有摘要。

建议下载 [v0.3.0 Windows 内含 Whisper 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.0/VideoSummarizer-v0.3.0-windows-x64-with-whisper.zip)，完整解压后双击 `VideoSummarizer.exe`。包含 Python 和 Whisper small；首次仍需同意下载其他依赖、Ollama 和摘要模型。较小的 [标准 Windows 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.3.0/VideoSummarizer-v0.3.0-windows-x64.zip)不包含 Whisper 模型。旧版下载保留在 Releases 历史记录。

已有摘要可点击「生成所选语言版本」。简繁转换通常无需模型；涉及英文或旧版没有独立摘要正文的输出，需要本机模型处理。原版与原始 SRT 保留，其他语言存放在任务的 `translations/语言代码/` 中，包含独立的 `summary.md` 与 `metadata.json`；生成过的版本可立即切换。来源标题、作者、网址、截图 SHA256 和精确时间戳保留原文。摘要仍可能有理解、翻译或专有名词错误，请核对原视频。浏览器、Windows 和 Streamlit 内置菜单不属于应用文字表；第三方原始错误写入日志，页面展示所选语言的处理建议。

升级请解压到新的可写入文件夹，不覆盖旧版；正常关闭旧版服务或重启 Windows 后再启动新版，避免共用端口冲突。可自行复制旧版 `outputs` 与完整的 `models` 文件夹。不会自动改写旧摘要或迁移系统设置。

## v0.2.1 及更早版本使用说明（历史）

**v0.2.1 提供 Windows x64 便攜版，內置 Python 3.11.17，無需預先安裝 Python。** 解壓後雙擊 `VideoSummarizer.exe`。首次使用仍需同意自動下載影片/語音依賴、Ollama、Node.js 和模型；完成後直接啟動本機網頁。沒有付費 API，不使用 Ollama cloud。

## 下載與安裝

### 一般使用者：免預裝 Python 的 Windows 便攜版

**無法連線 Hugging Face 的使用者可直接下載 [v0.2.1 內含 Whisper 版](https://github.com/leto0309/VideoSummarizer/releases/download/v0.2.1/VideoSummarizer-v0.2.1-windows-x64-with-whisper.zip)**（約 500 MB）。這是一個新資料夾使用的完整 Windows 安裝包：包含相同的 Python / EXE 和已驗證的 small 語音模型，解壓後雙擊 `VideoSummarizer.exe`，不用覆盖舊版或另行搬移語音模型。首次仍需同意自動下載其他依賴、Ollama 和摘要模型，這不是全部依賴預裝的完全離線包。若舊版仍在背景運行，先停止舊版專案服務或重啟 Windows，再開啟新資料夾；兩份不能同時占用相同服務埠。

下列標準便攜版約 47 MB，沒有內含語音模型：

1. 從 [Releases](https://github.com/leto0309/VideoSummarizer/releases) 下載 **VideoSummarizer-v0.2.1-windows-x64.zip**，完整解壓到有寫入權限的本機資料夾，勿直接在 ZIP 內執行。
2. 雙擊 **VideoSummarizer.exe**。首次會詢問是否允許下載免費依賴和模型；同意後在進度視窗自動配置，無需手動安裝 Python 或輸入 pip 指令。取消時不下載。
3. 配置成功後自動開啟瀏覽器。之後雙擊同一 EXE 即可啟動或重用此資料夾的背景服務。
4. 可選執行 `install-bookmark.bat` 安裝目前使用者的啟動書籤；需先完成首次配置。

便攜包內置完整 CPython、原生 .NET Framework 啟動器和預製 srt wheel；其餘 Python 套件、FFmpeg、Ollama、Node.js、CUDA 執行庫和模型於首次同意後下載到軟體資料夾。依賴採 wheel 安裝，首次配置不需編譯器。這不是完全離線包。目標 Windows 10 22H2 / Windows 11 x64（系統內建 .NET Framework 4.8）；不註冊系統 Python、不改全域 PATH、不需要管理員權限。使用 Astral python-build-standalone 20261009 的 CPython 3.11.17，構建時核對固定 SHA256。

進度視窗顯示配置與錯誤，進行中請保持開啟。成功後可關閉進度視窗，背景服務仍會運行；日誌保留在 `logs/`。首次配置嘗試預先下載 Whisper small；若 Hugging Face 無法連線，會顯示警告，仍允許處理有字幕的影片。無字幕影片需要先完成語音模型。可雙擊 `prepare-whisper.bat` 重試；既有摘要與模型保留。兩份資料夾仍共用固定服務埠，請勿同時啟動；未知服務不會被接管或關閉。

便攜版自動測試在解壓的發布 ZIP 中，直接以 EXE 啟動內置 Python，並移除 PATH 中的 Python 位置；檢查首次配置判斷、依賴安裝、單元測試、FFmpeg、Whisper 匯入、網頁載入及實際 HTTP 健康端點。此測試不下載模型、不驗證所有 GPU，也未自動操作桌面進度視窗。

### 開發者：原始碼版（仍需 Python）

1. 從 [Releases](https://github.com/leto0309/VideoSummarizer/releases) 下載原始碼 ZIP，解壓到你有寫入權限的本機資料夾，例如 `D:\VideoSummarizer`。首次發布前也可使用 GitHub 的 Code → Download ZIP。
2. 從 [Python 官方網站](https://www.python.org/downloads/windows/) 安裝 **Python 3.11、Windows 64 位**。保留 Python Launcher，或讓 `python` 指令指向 Python 3.11。
3. 雙擊 `setup.bat`，確認允許專案內下載。安裝器建立 `.venv`，下載 Ollama / Node.js、Python 依賴和預設模型；視網速可能需要較長時間與數 GB 流量。
4. 雙擊 `start.bat`，等待提示啟動成功，再開啟 <http://127.0.0.1:8501/>。請保持啟動視窗開啟。
5. 貼上影片連結，確認你有權處理內容，按「開始產生摘要」。

安裝器不安裝系統 CUDA Toolkit，不修改全域 PATH。FFmpeg 由 imageio-ffmpeg 套件提供。可選 CUDA 執行庫安裝失敗時，Whisper 回退 CPU；模型下載失敗會停止並顯示錯誤，重新執行 setup.bat 可重試。

首版固定 Ollama 0.40.2、Node.js 24.19.0 和 requirements.txt 的直接依賴版本；官方 ZIP 下載會驗證 SHA256。傳遞依賴與模型標籤由上游提供，未宣稱整個安裝環境逐位元可重現。

## 環境與模型

- 目標：Windows 10 22H2 / Windows 11，x64，Python 3.11；便攜版內置此環境，源碼版需自行安裝。其他系統未驗證。
- 建議 RAM 16 GB；磁碟建議至少預留 15 GB（依模型及依賴而變動）。這是建議配置，不是已驗證的最低需求。
- NVIDIA GPU 相容時 Whisper 使用 CUDA `int8_float16`；否則 CPU `int8`，CPU 處理長影片可能很慢。
- Whisper 預設 `small`，從官方 Hugging Face 倉庫下載到專案模型目錄（約 464 MiB）。完整本機模型優先使用，轉錄時不再檢查線上版本。
- Ollama 預設 `qwen3-vl:4b-instruct`；未偵測 NVIDIA GPU，或 VRAM 小於 6 GiB 時選擇 `qwen3-vl:2b-instruct`。CPU / 部分 GPU 推論速度取決於硬體。
- 上下文 4096 tokens；長字幕分段再合併。Whisper 和 Ollama 序列處理，跨頁面只允許一個摘要任務。
- 專案 Ollama 使用 `127.0.0.1:11435`，網頁使用 `127.0.0.1:8501`。這些是本機端點，不對外公開。

目前完整影片流程曾在一台 Windows / RTX 3050 Laptop 4 GB VRAM / 16 GB RAM 裝置驗證，包括字幕、CUDA / CPU 轉錄與畫面時間戳。這不代表所有裝置或每支平台影片都可用。GitHub 自動测试驗證程式邏輯，不執行模型推論或平台下載。

## 摘要與清理

先讀人工字幕，其次自動字幕；確實無字幕才下載音訊轉錄。可選下載低解析度影片，使用 FFmpeg 取得約 8 張均勻取樣畫面，時間取自實際解碼影格的 PTS。

成功產出保留在 `outputs/日期時間_任務ID/`：

- `summary.md`：影片資料、摘要、重點、概念解釋、字幕時間軸及畫面描述。
- `subtitles.srt`：原字幕或語音轉錄，保留來源时间以供核對。
- `metadata.json`：來源、模型、運算方式、實際畫面 PTS 及分析資訊。

成功寫入产出後，清理該任務影片、音訊與截圖；失敗暫存保留 24 小時。專案暫存上限 5 GB，只清理带專案標記的任務目錄，不刪模型或使用者其他檔案。

語音辨識和摘要都可能出錯，尤其是人名、專有名詞與低品質音訊。名稱修正必須有來源資料支持；摘要不能取代原影片核對。畫面抽樣不涵蓋整支影片。

## Chrome 啟動書籤（選用）

1. 完成 setup.bat 後，雙擊 `install-bookmark.bat`，註冊目前使用者的自訂連結。
2. 在 Chrome 書籤管理員新增書籤，網址填 `videosummarizer://open`。
3. 點書籤並確認開啟外部應用。因啟動器是 Python，提示可能顯示 Python。

服務已運行就直接開啟，未運行則背景啟動並等待就緒。冷啟動可能需要約兩分鐘；進度記錄於 `logs/bookmark.log` 和 `logs/startup.log`。Chrome 不接受直接協議書籤時，可收藏專案內的 `bookmark.html` 並點按鈕。

書籤模式沒有開機自啟；關閉網頁不會停止背景服務。要移除連結註冊，執行 `remove-bookmark.bat`；模型與摘要保留。啟動器採用系統預設瀏覽器，不包含發布者的 Chrome 路徑或個人設定。

## 常見問題

### Whisper 下載逾時 / WinError 10060 / LocalEntryNotFoundError

這表示無法取得語音模型且本機沒有完整快取；不是 CUDA 計算失敗。改用 CPU 不會修復網路。網頁能開啟不代表所有 AI 模型均已下載。

1. 確認能開啟 [官方 small 模型頁面](https://huggingface.co/Systran/faster-whisper-small)。首次下載模型需要網路，推論本身在本機執行。
2. 在軟體資料夾雙擊 `prepare-whisper.bat`，同意下載後等待完成。使用內置 Python，不需安裝系統 Python。失敗原因記錄於 `logs/whisper-download.log`，部分下載檔案保留供重試。
3. 若該電腦無法連線，可在能下載的電腦完成這一步，關閉下載程式後，將**整個 `models/whisper` 資料夾**複製到另一台軟體資料夾下的同名位置。若來源快取使用符號連結，請複製實際檔案內容，避免斷鏈。
4. 也可從官方模型頁面下載同一版本的 `model.bin`、`config.json`、`tokenizer.json`、`vocabulary.txt`（或 `vocabulary.json`），放到 `models/whisper/small/`；若上游提供 `preprocessor_config.json`，一併複製。請使用 faster-whisper 的 CTranslate2 模型，OpenAI 原始 `.pt` 檔不能直接使用。
5. 再執行 `prepare-whisper.bat`。本機完整檔案會直接通過檢查，不連線下載。網頁也顯示模型檔案是否就緒；實際權重是否有效仍由推論時的原生模型載入驗證。

v0.2.0 使用者可下載 v0.2.1 **source.zip**，將其中 `VideoSummarizer` 資料夾內的程式檔覆蓋到既有軟體目錄。便攜版保留原有 `VideoSummarizer.exe`、`runtime`、`tools`、`models`、`outputs` 與 `portable-ready.json`，不需要重裝 Python 或 Ollama。完成後執行 `prepare-whisper.bat`；關閉原來的網頁並重新開啟以載入新版。自訂修改過的原始碼請先備份。修正網路錯誤提示不能保證 Hugging Face 在每個網路環境都可連線。

### 其他問題

- **第一次啟動沒有反應**：先確認瀏覽器的「開啟 Python」提示；Ollama 初始化期間查看 `logs/startup.log`。Streamlit 郵箱提示已明確關閉。
- **端口已使用**：確認是否仍有此專案或其他服務運行。未知 Ollama 服务會被拒絕，不會自動結束他人的程序。
- **CUDA 失敗**：工具嘗試回退 CPU。用 `.venv\Scripts\python.exe diagnostics.py` 收集本機診斷；提交問題前刪掉私密資料及本機路徑。
- **平台下載失敗**：平台規則會變動；yt-dlp 固定為已測試 nightly 版本。若遇登入、付費、驗證或其他限制，工具停止，不繞過。
- **更新**：把新版本解壓至新資料夾並重新 setup，或保留原目錄的 models / outputs 後按文檔升級。不要把其他電腦的 `.venv` 直接複製過來。

## 開發與貢獻

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

測試不需要下载 AI 模型。安裝和實際推論是另一項驗證，請參考 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 使用範圍與隱私

僅處理你有權合法存取的內容。不讀取瀏覽器 cookies，不使用帳密，不繞過 DRM、付費、登入、驗證或區域限制。下載器只允許 HTTPS Bilibili / b23.tv / YouTube 連結。

Ollama cloud 已禁用；字幕和畫面只送至專案的本機 Ollama。原始平台、GitHub、PyPI、Node.js、Ollama 模型庫與 Hugging Face 仍會收到必要下載請求。執行檔和模型首次下載需使用者同意。

專案代码採 [MIT](LICENSE)。第三方程式、套件與模型保留自己的授權，詳見 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。源碼 ZIP 不含第三方二進位或模型權重；Windows 便攜 ZIP 另含 CPython 及其上游授權，不含 AI 模型或下載影片。
