@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Running Codex token usage script...
echo.

if not exist "%~dp0codex_tokens.ps1" (
    echo ERROR: PowerShell script was not found:
    echo %~dp0codex_tokens.ps1
    echo.
    dir /b
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0codex_tokens.ps1" -SinceDays 40 -AlignWindow 2

echo.
echo Script finished.
pause