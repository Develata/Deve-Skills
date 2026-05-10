@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Running Codex token usage script...
echo.

if not exist "%~dp0codex_tokens.py" (
    echo ERROR: Python script was not found:
    echo %~dp0codex_tokens.py
    echo.
    dir /b
    echo.
    pause
    exit /b 1
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python "%~dp0codex_tokens.py" collect --since-days 40 --align-window 2
) else (
    py -3 "%~dp0codex_tokens.py" collect --since-days 40 --align-window 2
)

if errorlevel 1 (
    echo.
    echo Script failed.
    pause
    exit /b %errorlevel%
)

echo.
echo Script finished.
pause
