@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "VSPY=.venv\Scripts\python.exe"
if exist "runtime\python.exe" set "VSPY=runtime\python.exe"
"%VSPY%" register_bookmark.py
if errorlevel 1 (
  pause
  exit /b 1
)
echo Bookmark address: videosummarizer://open
pause
