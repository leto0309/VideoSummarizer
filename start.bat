@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set OLLAMA_NO_CLOUD=1
if not exist ".venv\Scripts\python.exe" (
  echo Run setup.bat first.
  pause
  exit /b 1
)
echo Opening local interface: http://127.0.0.1:8501
".venv\Scripts\python.exe" launcher.py
if errorlevel 1 pause
