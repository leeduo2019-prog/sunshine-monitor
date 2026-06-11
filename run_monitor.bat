@echo off
REM ============================================================
REM 阳光平台监控 - 手动/计划任务运行入口
REM 使用 %~dp0 自适应项目路径，可在任意目录部署
REM ============================================================

setlocal

REM 切到脚本所在目录（项目根）
cd /d "%~dp0"

REM 创建日志目录
if not exist "logs" mkdir "logs"

REM 日志文件：logs\monitor_<日期>.log
for /f "tokens=1-3 delims=/" %%a in ("%date%") do set LOG_DATE=%%a-%%b-%%c
set LOG_FILE=%~dp0logs\monitor_%LOG_DATE%.log

echo ============================================================ >> "%LOG_FILE%"
echo [%date% %time%] 启动阳光平台监控 >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

REM 检查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装或不在 PATH 中 >> "%LOG_FILE%"
    echo [%date% %time%] [ERROR] Python not found >> "%LOG_FILE%"
    exit /b 1
)

REM 检查主入口
if not exist "src\main.py" (
    echo [ERROR] src\main.py 不存在，当前目录: %CD% >> "%LOG_FILE%"
    exit /b 1
)

REM 执行主程序（输出同时写控制台与日志）
python src\main.py >> "%LOG_FILE%" 2>&1
set EXIT_CODE=%errorlevel%

echo [%date% %time%] 任务结束，退出码 %EXIT_CODE% >> "%LOG_FILE%"

endlocal & exit /b %EXIT_CODE%