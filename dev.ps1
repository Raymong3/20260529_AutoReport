# 백엔드(FastAPI) + 프론트엔드(Vite) 동시 실행
$root = $PSScriptRoot

Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "Write-Host '[백엔드] 시작 중...' -ForegroundColor Cyan; " + `
  "Set-Location '$root\backend'; " + `
  ".\venv\Scripts\uvicorn.exe main:app --reload"

Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "Write-Host '[프론트엔드] 시작 중...' -ForegroundColor Green; " + `
  "Set-Location '$root\frontend'; " + `
  "npm run dev"

Write-Host ""
Write-Host "두 서버가 새 창에서 실행됩니다." -ForegroundColor Yellow
Write-Host "  백엔드:    http://localhost:8000" -ForegroundColor Cyan
Write-Host "  프론트엔드: http://localhost:5173" -ForegroundColor Green
