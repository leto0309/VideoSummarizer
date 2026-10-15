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
  echo Complete first-time setup first ^(VideoSummarizer.exe or setup.bat^).
  pause
  exit /b 1
)
rem The menu is shown by Python in the page language.
"%VSPY%" ytdlp_update.py --ask
set "result=%errorlevel%"
pause
exit /b %result%
