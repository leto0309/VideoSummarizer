@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if exist "VideoSummarizer.exe" (
  start "" "VideoSummarizer.exe" --install-gpu
  exit /b 0
)
if not exist ".venv\Scripts\python.exe" (
  echo 请先运行 setup.bat 完成 CPU 模式配置。
  echo Run setup.bat first to complete the CPU setup.
  pause
  exit /b 1
)
set "PYTHONIOENCODING=utf-8"
rem gpu_setup.py asks for consent in the page language.
".venv\Scripts\python.exe" gpu_setup.py --ask
set "gpu_result=%errorlevel%"
pause
exit /b %gpu_result%
