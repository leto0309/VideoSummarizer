@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONNOUSERSITE=1
set "PYTHONHOME="
set "PYTHONPATH="
rem Works before first-time setup: the check uses only the Python standard library.
set "CHECK_PYTHON=py -3.11"
if exist ".venv\Scripts\python.exe" set "CHECK_PYTHON=.venv\Scripts\python.exe"
if exist "runtime\python.exe" set "CHECK_PYTHON=runtime\python.exe"
%CHECK_PYTHON% network_check.py
echo Results are saved in logs\network-check.json.
pause
