@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
".venv\Scripts\python.exe" register_bookmark.py
if errorlevel 1 (
  pause
  exit /b 1
)
echo Bookmark address: videosummarizer://open
pause
