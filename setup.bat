@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo VideoSummarizer setup downloads free dependencies and local AI models.
echo Downloads can require several GB. No paid API or cloud inference.
choice /c YN /m "Allow project-local installation and downloads"
if errorlevel 2 exit /b 1
py -3.11 -c "import sys; assert sys.version_info[:2] == (3,11) and sys.maxsize > 2**32" >nul 2>&1
if not errorlevel 1 (
  py -3.11 -m venv .venv
) else (
  python -c "import sys; assert sys.version_info[:2] == (3,11) and sys.maxsize > 2**32" >nul 2>&1
  if errorlevel 1 goto missingpython
  python -m venv .venv
)
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --no-cache-dir --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" setup_runtime.py
if errorlevel 1 goto failed
".venv\Scripts\python.exe" diagnostics.py
if errorlevel 1 goto failed
echo Setup complete. Run start.bat. Keep the startup window open.
pause
exit /b 0
:missingpython
echo Install 64-bit Python 3.11 from python.org, then run this setup again.
pause
exit /b 1
:failed
echo Setup stopped. Existing outputs and models are preserved. Read the error above.
pause
exit /b 1
