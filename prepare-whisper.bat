@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONNOUSERSITE=1
set "PYTHONHOME="
set "PYTHONPATH="
set "WHISPER_PYTHON=.venv\Scripts\python.exe"
if exist "runtime\python.exe" set "WHISPER_PYTHON=runtime\python.exe"
if not exist "%WHISPER_PYTHON%" (
  echo Run setup.bat or VideoSummarizer.exe first.
  pause
  exit /b 1
)
"%WHISPER_PYTHON%" whisper_models.py --check
if not errorlevel 1 goto ready
echo Download Whisper small from Hugging Face, about 464 MiB, into models\whisper.
echo You may instead copy models\whisper from a computer that has completed the download.
choice /c YN /m "Allow this project-local model download"
if errorlevel 2 exit /b 1
"%WHISPER_PYTHON%" whisper_models.py
if errorlevel 1 (
  echo Model is not ready. Read the message above and logs\whisper-download.log.
  pause
  exit /b 1
)
:ready
echo Whisper small is ready. You can now process videos without subtitles.
pause
exit /b 0
