@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONNOUSERSITE=1
set "PYTHONHOME="
set "PYTHONPATH="
set "VSPY=.venv\Scripts\python.exe"
if exist "runtime\python.exe" set "VSPY=runtime\python.exe"
if not exist "%VSPY%" (
  echo 请先完成首次配置（VideoSummarizer.exe 或 setup.bat）。
  pause
  exit /b 1
)
echo 视频下载组件 yt-dlp：平台改版导致视频无法读取时，可以更新到最新版本。
echo U = 更新到最新版本（从 PyPI 下载，只装在本软件文件夹里）
echo R = 恢复本版本测试过的 yt-dlp
choice /c URC /m "更新(U)、恢复(R) 或取消(C)"
if errorlevel 3 exit /b 1
if errorlevel 2 goto restore
"%VSPY%" ytdlp_update.py
goto done
:restore
"%VSPY%" ytdlp_update.py --restore
:done
set "result=%errorlevel%"
pause
exit /b %result%
