@echo off
REM Run live_sniffer with the project venv (torch, etc.) — use this from Admin CMD
REM so you do not accidentally invoke a system Python without packages.
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo ERROR: venv not found. Run: python -m venv venv ^&^& venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)
"%~dp0venv\Scripts\python.exe" "%~dp0live_sniffer.py" %*
set EXITCODE=%ERRORLEVEL%
if %EXITCODE% neq 0 pause
exit /b %EXITCODE%
