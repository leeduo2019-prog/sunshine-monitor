@echo off
echo ============================================================
echo Sunlight Platform Monitor - Auto Deployment
echo ============================================================
echo.
echo Schedule:
echo   - Daily 09:30
echo   - Daily 21:30
echo.
echo Press any key to continue (Requires Admin)...
pause >nul
echo.

REM Check Admin
net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Please run as Administrator!
    pause
    exit /b 1
)

echo [1/4] Checking environment...
cd /d "%~dp0"

if not exist "src\main.py" (
    echo [ERROR] src\main.py not found.
    pause
    exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

echo OK Python found.
echo.

echo [2/4] Cleaning old tasks...
schtasks /delete /tn "SunlightMonitor_AM" /f >nul 2>&1
schtasks /delete /tn "SunlightMonitor_PM" /f >nul 2>&1
echo OK Old tasks removed.
echo.

set SCRIPT_PATH=%~dp0run_monitor.bat

echo [3/4] Creating AM task (09:30)...
schtasks /create /tn "SunlightMonitor_AM" /tr "%SCRIPT_PATH%" /sc daily /st 09:30 /rl highest /f
if errorlevel 1 (
    echo [ERROR] AM task creation failed.
) else (
    echo OK AM task created.
)
echo.

echo [4/4] Creating PM task (21:30)...
schtasks /create /tn "SunlightMonitor_PM" /tr "%SCRIPT_PATH%" /sc daily /st 21:30 /rl highest /f
if errorlevel 1 (
    echo [ERROR] PM task creation failed.
) else (
    echo OK PM task created.
)
echo.

echo ============================================================
echo Deployment Complete!
echo ============================================================
echo.
echo Tasks created:
echo   1. SunlightMonitor_AM (09:30)
echo   2. SunlightMonitor_PM (21:30)
echo.
echo To verify:
echo   1. Press Win+R, type taskschd.msc
echo   2. Find tasks named SunlightMonitor_AM/PM
echo   3. Right-click - Run to test.
echo.
pause
