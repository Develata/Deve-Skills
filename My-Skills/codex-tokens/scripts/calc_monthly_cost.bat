@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Calculating monthly CostUSD...
echo.

if not exist "%~dp0calc_monthly_cost.ps1" (
    echo ERROR: PowerShell script was not found:
    echo %~dp0calc_monthly_cost.ps1
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0calc_monthly_cost.ps1"

echo.
echo Script finished.
pause