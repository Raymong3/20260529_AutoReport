@echo off
echo [K-water] 기존 서버 프로세스 종료 중...

REM 1. uvicorn 프로세스 전체 종료
taskkill /F /IM uvicorn.exe >nul 2>&1

REM 2. 포트 8000 리스닝 프로세스 종료 (uvicorn 워커 포함)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM 3. 잔여 워커가 정리될 때까지 대기 후 재확인
timeout /t 2 /nobreak >nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo [K-water] 서버 시작 중...
start "backend" /D "%~dp0backend" cmd /k "venv\Scripts\uvicorn.exe main:app --reload"
start "frontend" /D "%~dp0frontend" cmd /k "npm run dev"
