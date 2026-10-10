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
  pause
  exit /b 1
)
choice /c YN /m "Allow optional project-local CUDA downloads, over 1 GB"
if errorlevel 2 exit /b 1
set "PYTHONIOENCODING=utf-8"
".venv\Scripts\python.exe" gpu_setup.py
set "gpu_result=%errorlevel%"
pause
exit /b %gpu_result%
