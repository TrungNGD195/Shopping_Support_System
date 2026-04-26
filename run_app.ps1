# Script khởi động tự động hệ thống Shopping Support System (React + FastAPI)

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   KHOI DONG SHOPPING SUPPORT SYSTEM (SAAS VERSION)   " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = $PSScriptRoot

# Kiem tra thu muc frontend
$FrontendDir = "$ProjectRoot\src\frontend"
if (-not (Test-Path "$FrontendDir\node_modules")) {
    Write-Host "[0/3] Chua co node_modules, dang cai dat..." -ForegroundColor Yellow
    cmd /c "cd /d `"$FrontendDir`" && npm install"
}

# 1. Cai dat thu vien Python
Write-Host "[1/3] Kiem tra va cai dat dependencies Backend..." -ForegroundColor Yellow
pip install -r "$ProjectRoot\requirements.txt" -q

# 2. Khoi dong FastAPI Backend trong cua so moi
Write-Host "[2/3] Dang khoi dong FastAPI Backend (Port 8000)..." -ForegroundColor Yellow
$BackendProcess = Start-Process -FilePath "cmd" `
    -ArgumentList "/c cd /d `"$ProjectRoot`" && python -m uvicorn src.api_server:app --reload --port 8000" `
    -PassThru -NoNewWindow

# Doi Backend nap xong model AI (~10 giay)
Write-Host "   Dang cho Backend nap model AI..." -ForegroundColor DarkGray
Start-Sleep -Seconds 10

# 3. Khoi dong React Frontend
Write-Host "[3/3] Dang khoi dong React Web App (Port 5173)..." -ForegroundColor Yellow
$FrontendProcess = Start-Process -FilePath "cmd" `
    -ArgumentList "/c cd /d `"$FrontendDir`" && npm run dev -- --open" `
    -PassThru -NoNewWindow

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "   HE THONG DA HOAT DONG!                             " -ForegroundColor Green
Write-Host "   - API Docs   : http://localhost:8000/docs          " -ForegroundColor Green
Write-Host "   - Giao dien  : http://localhost:5173               " -ForegroundColor Green
Write-Host "   Nhan Ctrl+C de tat toan bo he thong.               " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green

try {
    # Giu script chay cho den khi nguoi dung nhan Ctrl+C
    while ($true) { Start-Sleep -Seconds 5 }
} finally {
    Write-Host ""
    Write-Host "Dang tat he thong..." -ForegroundColor Red
    if ($BackendProcess -and !$BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "   [OK] Da tat Backend." -ForegroundColor DarkGray
    }
    if ($FrontendProcess -and !$FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "   [OK] Da tat Frontend." -ForegroundColor DarkGray
    }
    Write-Host "Da tat an toan." -ForegroundColor Green
}
