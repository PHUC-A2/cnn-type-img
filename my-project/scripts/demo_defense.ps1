# Script demo bảo vệ đồ án — CNN Vision Platform
# Chạy: .\scripts\demo_defense.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CNN Vision Platform — Demo Bao Ve" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $Python)) {
    Write-Host "[LOI] Chua co .venv. Chay:" -ForegroundColor Red
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    Write-Host "  .\.venv\Scripts\pip install -r requirements\base.txt" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
    Write-Host "[CANH BAO] Chua co file .env — sao chep tu .env.example" -ForegroundColor Yellow
    Copy-Item (Join-Path $ProjectRoot ".env.example") (Join-Path $ProjectRoot ".env")
}

Write-Host "[1/4] Khoi tao database..." -ForegroundColor Green
& $Python manage.py init_db

Write-Host ""
Write-Host "[2/4] Chay test E2E (Phase 10)..." -ForegroundColor Green
& $Python manage.py test tests.test_phase10_e2e -v 1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[CANH BAO] Mot so test that bai — kiem tra MySQL va .env" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/4] Khoi dong server..." -ForegroundColor Green
Write-Host "  URL: http://127.0.0.1:8000/" -ForegroundColor White
Write-Host "  Admin: admin / admin123 (tu .env)" -ForegroundColor White
Write-Host ""

Write-Host "[4/4] Kich ban demo truoc hoi dong:" -ForegroundColor Green
Write-Host ""
Write-Host "  BUOC 1 — Dang nhap admin" -ForegroundColor Cyan
Write-Host "    -> /auth/dang-nhap/  (admin / admin123)"
Write-Host ""
Write-Host "  BUOC 2 — Upload dataset" -ForegroundColor Cyan
Write-Host "    -> /datasets/upload/"
Write-Host "    -> ZIP: moi thu muc = 1 class, toi thieu 2 class, 2 anh/class"
Write-Host "    -> Vi du: cat/img1.png, dog/img1.png"
Write-Host ""
Write-Host "  BUOC 3 — Huan luyen CNN" -ForegroundColor Cyan
Write-Host "    -> /training/"
Write-Host "    -> Chon dataset, dat epoch=5-10, bat dau huan luyen"
Write-Host "    -> Theo doi tien trinh tai /training/<job_id>/"
Write-Host ""
Write-Host "  BUOC 4 — Phan loai anh" -ForegroundColor Cyan
Write-Host "    -> /predict/"
Write-Host "    -> Chon model da huan luyen, upload anh test"
Write-Host "    -> Xem nhan + do tin cay + bieu do xac suat"
Write-Host ""
Write-Host "  BUOC 5 — Lich su & Phan tich" -ForegroundColor Cyan
Write-Host "    -> /history/       — Lich su du doan"
Write-Host "    -> /analytics/     — Bieu do accuracy, confusion matrix"
Write-Host ""
Write-Host "  BUOC 6 — Admin panel (vai tro admin)" -ForegroundColor Cyan
Write-Host "    -> /admin-panel/           — Tong quan he thong"
Write-Host "    -> /admin-panel/users/     — Quan ly nguoi dung"
Write-Host "    -> /admin-panel/logs/      — Log he thong & request"
Write-Host ""
Write-Host "Nhan Ctrl+C de dung server." -ForegroundColor DarkGray
Write-Host ""

& $Python manage.py runserver
