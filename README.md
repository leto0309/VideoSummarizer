# VideoSummarizer

Windows 免費本機影片摘要工具：Bilibili / b23.tv / YouTube、字幕優先、繁體中文摘要、可選畫面分析。

**v0.2.0 提供 Windows x64 便攜版，內置 Python 3.11.17，無需預先安裝 Python。** 解壓後雙擊 `VideoSummarizer.exe`。首次使用仍需同意自動下載影片/語音依賴、Ollama、Node.js 和模型；完成後直接啟動本機網頁。沒有付費 API，不使用 Ollama cloud。

## 下載與安裝

### 一般使用者：免預裝 Python 的 Windows 便攜版

1. 從 [Releases](https://github.com/leto0309/VideoSummarizer/releases) 下載 **VideoSummarizer-v0.2.0-windows-x64.zip**，完整解壓到有寫入權限的本機資料夾，勿直接在 ZIP 內執行。
2. 雙擊 **VideoSummarizer.exe**。首次會詢問是否允許下載免費依賴和模型；同意後在進度視窗自動配置，無需手動安裝 Python 或輸入 pip 指令。取消時不下載。
3. 配置成功後自動開啟瀏覽器。之後雙擊同一 EXE 即可啟動或重用此資料夾的背景服務。
4. 可選執行 `install-bookmark.bat` 安裝目前使用者的啟動書籤；需先完成首次配置。

便攜包內置完整 CPython、原生 .NET Framework 啟動器和預製 srt wheel；其餘 Python 套件、FFmpeg、Ollama、Node.js、CUDA 執行庫和模型於首次同意後下載到軟體資料夾。依賴採 wheel 安裝，首次配置不需編譯器。這不是完全離線包。目標 Windows 10 22H2 / Windows 11 x64（系統內建 .NET Framework 4.8）；不註冊系統 Python、不改全域 PATH、不需要管理員權限。使用 Astral python-build-standalone 20261009 的 CPython 3.11.17，構建時核對固定 SHA256。

進度視窗顯示配置與錯誤，進行中請保持開啟。成功後可關閉進度視窗，背景服務仍會運行；日誌保留在 `logs/`。首次語音轉錄再下載 Whisper small。下載失敗可重新啟動重試，既有摘要與模型保留。兩份資料夾仍共用固定服務埠，請勿同時啟動；未知服務不會被接管或關閉。

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
- Whisper 預設 `small`，首次無字幕轉錄時自動從 Hugging Face 下載到專案模型目錄。
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
