@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHONW=%ROOT%.venv\Scripts\pythonw.exe"

if not exist "%PYTHONW%" (
    echo Finecut virtual environment not found at "%PYTHONW%".
    echo Run: .venv\Scripts\python.exe -m pip install -e ".[dev]"
    pause
    exit /b 1
)

start "" "%PYTHONW%" -m finecut.main
endlocal
