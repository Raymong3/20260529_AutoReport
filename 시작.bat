@echo off
title K-water Report Assistant

set "ROOT=%~dp0"

echo.
echo  ====================================
echo   K-water Report Assistant Starting
echo  ====================================
echo.

REM Check port 8000 (backend)
netstat -ano | findstr ":8000 " | findstr LISTENING > nul
if %errorlevel% == 0 (
    echo  [SKIP] Port 8000 already in use. Reusing existing backend.
    goto frontend
)

echo  [1/3] Starting backend server on port 8000...
start "Backend :8000" /d "%ROOT%backend" cmd /k "venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak > nul

REM Check port 5173 (frontend)
:frontend
netstat -ano | findstr ":5173 " | findstr LISTENING > nul
if %errorlevel% == 0 (
    echo  [SKIP] Port 5173 already in use. Reusing existing frontend.
    goto open_browser
)

echo  [2/3] Starting frontend server on port 5173...
start "Frontend :5173" /d "%ROOT%frontend" cmd /k "npm run dev"

echo  [3/3] Waiting 5 seconds for servers to start...
timeout /t 5 /nobreak > nul

REM Open browser
:open_browser
echo  Opening browser...
start http://localhost:5173

echo.
echo  Done!
echo    Backend  : http://127.0.0.1:8000
echo    Frontend : http://localhost:5173
echo.
echo  To stop: close the Backend and Frontend windows.
echo  Press any key to close this launcher.
echo.
pause > nul
