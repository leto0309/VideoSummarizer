# VideoSummarizer 进度

接手这个项目的人或 Agent 先读这里，再读 CONTRIBUTING.md 和 CHANGELOG.md。完成任务时在同一个提交或 PR 里更新本文件，只写现在的状态。

## 当前版本

- 已发布：v0.3.11（2026-10-16），标签指向 `286ff07`。
- 附件：完整源码包，Windows 标准版、含 Whisper 版、含 Whisper 与 Ollama 版三个 ZIP，以及各自的 `*SHA256SUMS.txt`。
- 自 v0.3.11 以来没有尚未发布的改动。

## 进行中

- 无。

## 待办

- 2B 模型仍会在画面说明开头加上「# 画面描述」之类的标题，不理会“不要标题”的提示；目前靠 0.3.8 加入的报告整理去掉。若换用更大的模型，再确认是否还需要这层整理。
- 最近几个版本只经过 Claude 与 Gemini 4 Argon 审查；Codex 额度恢复后可以补做一次独立审查。

## 最近的决定

- 0.3.11：下载中途断线时最多重试 10 次、间隔逐步拉长；网络问题显示“网络暂时不稳定”，不再建议更新 yt-dlp。
- 0.3.10：首次配置可选简体中文、繁體中文或 English；新增英文 README，旧版说明集中在 CHANGELOG。
- 0.3.9：所有依赖锁定版本和哈希（`requirements.lock`、`requirements-gpu.lock`），安装一律用 `--require-hashes`；改依赖后用 `scripts/lock_requirements.py` 重新生成，不手改锁文件。
- 不登录平台账号、不绕过平台限制；遇到平台风控时只提示稍后再试或更新 yt-dlp。

## 发布流程要点

1. 在功能分支更新 `app_version.py`、CHANGELOG、README.md 与 README.en.md 的当前版本段落，开 PR，Windows CI 通过后合并。
2. 运行源码发布（`source-release.yml`）和 Windows 便携版发布（`windows-portable.yml`）工作流。
3. 发布后运行 `python scripts/verify_release.py vX.Y.Z` 核对已发布的文件，再补写 Release 说明。
4. 发布包里不能有个人的书签设置文件或运行时的 PID 与归属文件（见 CONTRIBUTING.md）。

## 历史

- v0.3.11：下载断线自动重试，网络问题的提示更准确。
- v0.3.10：首次配置的语言选择，英文 README。
- v0.3.9：依赖全部锁定哈希。
- v0.3.8：平台没有可下载媒体时的说明、报告标题整理、`verify_release.py`。
