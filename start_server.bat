@echo off
setlocal
title FitNesse Test Automation Server (SECURE)
echo =====================================================================
echo  Starting FitNesse + Python API and UI Automation Server
echo  [SECURITY] Authentication is ENABLED. Login required to access portal.
echo =====================================================================

cd /d "%~dp0"
set "PYTHONPATH=%~dp0"
echo [INFO] PYTHONPATH set to: %PYTHONPATH%

rem Check .env presence
if not exist ".env" (
    echo [WARNING] .env file not found. Copying .env.example...
    copy ".env.example" ".env" >nul
)

rem Activate Python Virtual Environment
if exist "%~dp0.venv\Scripts\activate.bat" (
    echo [INFO] Activating Python virtual environment [.venv]...
    call "%~dp0.venv\Scripts\activate.bat"
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    echo [WARNING] Python virtual environment [.venv] not found.
    set "PYTHON_EXE=python"
)

rem Ensure Playwright browsers are installed for UI automation
"%PYTHON_EXE%" -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(headless=True).close(); p.stop()" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Playwright browser binaries missing. Downloading Chromium...
    "%PYTHON_EXE%" -m playwright install chromium
)

rem Automatically terminate any old Java/FitNesse/Mock/UserStore processes holding ports
echo [INFO] Scanning and clearing ports 8080, 8085, 8089, and 8090...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :8080') do if not "%%a"=="0" taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :8085') do if not "%%a"=="0" taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :8089') do if not "%%a"=="0" taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :8090') do if not "%%a"=="0" taskkill /f /pid %%a >nul 2>&1

rem Clean old report results
del /q /s "%~dp0FitNesseRoot\files\testResults\allure-results\*" >nul 2>&1
del /q /s "%~dp0FitNesseRoot\files\testResults\allure-report\*" >nul 2>&1

rem Determine Java executable
set "JAVA_CMD=java"
if defined JAVA_HOME (
    if exist "%JAVA_HOME%\bin\java.exe" (
        set "JAVA_CMD=%JAVA_HOME%\bin\java.exe"
    )
)

rem Check if Java is installed
"%JAVA_CMD%" -version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Java is not installed or not in system PATH.
    echo [ERROR] FitNesse requires Java 8 or higher to run.
    pause
    exit /b 1
)

rem Start Background Services
echo [INFO] Starting JSON-backed User Store Server on port 8090...
start "User Store Server" /b "%PYTHON_EXE%" "%~dp0core\user_store_server.py"

echo [INFO] Starting Real-Time Folder-Sync Self-Healing Watcher in background...
start "FitNesse Watcher" /b "%PYTHON_EXE%" "%~dp0core\fitnesse_watcher.py"

rem Launch FitNesse Server
echo [INFO] Launching FitNesse Portal on http://localhost:8080/
echo [INFO] Press Ctrl+C in this terminal to stop the server.
echo ---------------------------------------------------------------------

"%JAVA_CMD%" -Dfitnesse.runner.parallel=1 -Duser.timezone=Asia/Kolkata -Dsun.timezone.ids.oldmapping=false -Dprevent.system.exit=false -Dfitnesse.security.manager.enabled=false --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED -cp "%~dp0.;%~dp0fitnesse-standalone.jar" fitnesseMain.FitNesseMain -p 8080 -a "%~dp0passwords.txt"

