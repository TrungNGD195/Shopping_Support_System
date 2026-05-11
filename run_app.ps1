# Script khởi động tự động hệ thống Shopping Support System (React + FastAPI)

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   KHOI DONG SHOPPING SUPPORT SYSTEM (SAAS VERSION)   " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = $PSScriptRoot

# Đảm bảo cài đặt đủ thư viện Python (nếu chưa có)
Write-Host "[1/3] Kiem tra va cai dat dependencies Backend..." -ForegroundColor Yellow
pip install -r requirements.txt -q

# Khởi động FastAPI Backend trong một background process
Write-Host "[2/3] Dang khoi dong FastAPI Backend (Port 8000)..." -ForegroundColor Yellow
$BackendProcess = Start-Process -FilePath "python" -ArgumentList "-m uvicorn src.api_server:app --reload --port 8000" -PassThru -NoNewWindow

# Đợi một chút cho Backend nạp model
Start-Sleep -Seconds 5

# Khởi động React Vite Frontend
Write-Host "[3/3] Dang khoi dong React Web App (Port 5173)..." -ForegroundColor Yellow
Set-Location -Path "$ProjectRoot\src\frontend"
$FrontendProcess = Start-Process -FilePath "npm" -ArgumentList "run dev -- --open" -PassThru -NoNewWindow
Set-Location -Path $ProjectRoot

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "   HE THONG DA HOAT DONG!                             " -ForegroundColor Green
Write-Host "   - API Docs: http://localhost:8000/docs             " -ForegroundColor Green
Write-Host "   - Giao dien Web: http://localhost:5173             " -ForegroundColor Green
Write-Host "   Nhan Ctrl+C hoac tat cua so de thoat.              " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green

try {
    Wait-Process -Id $FrontendProcess.Id
} finally {
    Write-Host "Dang tat he thong..." -ForegroundColor Red
    if ($BackendProcess -and !$BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force
    }
    if ($FrontendProcess -and !$FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force
    }
    Write-Host "Da tat an toan." -ForegroundColor Green
}
