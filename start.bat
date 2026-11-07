@echo off
setlocal
title PneumoScan AI
cd /d "%~dp0"

echo.
echo   PneumoScan AI - Pneumonia Detection using ResNet
echo   ================================================
echo.

if not exist ".venv\Scripts\python.exe" goto :novenv
if exist "app\frontend\dist\index.html" goto :run

echo   The web interface is not built yet. Building it now (one time only)...
where npm >nul 2>nul
if errorlevel 1 goto :nonode
pushd "app\frontend"
if not exist "node_modules" call npm install --no-audit --no-fund
if errorlevel 1 goto :buildfail
call npm run build
if errorlevel 1 goto :buildfail
popd

:run
".venv\Scripts\python.exe" -X utf8 "app\backend\launcher.py" %*
if errorlevel 1 goto :fail
exit /b 0

:novenv
echo   [ERROR] The Python environment was not found: .venv\Scripts\python.exe
echo   Set it up first. See README.md, section "First-time setup".
goto :fail

:nonode
echo   [ERROR] Node.js (npm) was not found, so the web interface cannot be built.
echo   Install Node.js, then run in app\frontend:  npm install  and  npm run build
goto :fail

:buildfail
popd
echo   [ERROR] Building the web interface failed. See the messages above.
goto :fail

:fail
echo.
echo   PneumoScan AI could not start. Read the message above, then press any key to close.
pause >nul
exit /b 1
