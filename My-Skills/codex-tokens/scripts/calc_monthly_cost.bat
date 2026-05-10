@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Calculating monthly CostUSD...
echo.

if not exist "%~dp0calc_monthly_cost.py" (
    echo ERROR: Python script was not found:
    echo %~dp0calc_monthly_cost.py
    echo.
    pause
    exit /b 1
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python "%~dp0calc_monthly_cost.py"
) else (
    py -3 "%~dp0calc_monthly_cost.py"
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
