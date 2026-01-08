@echo off
REM Windows Launcher for Steam Deck Repo Manager

pushd "%~dp0"

REM Check if uv is installed
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 'uv' is not installed or not in your PATH.
    echo Please install uv via PowerShell:
    echo powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    popd
    exit /b
)

echo Syncing dependencies...
set UV_PROJECT_ENVIRONMENT=.venv_win
uv sync

echo Starting Steam Deck Repo Manager...
uv run python -m src.main

popd
if %errorlevel% neq 0 pause
