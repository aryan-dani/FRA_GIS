# Start FRA Atlas frontend + backend together (Windows PowerShell).
# Usage (from repo root):
#   .\start-dev.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating .venv ..." -ForegroundColor Cyan
    python -m venv .venv
    & $VenvPython -m pip install --upgrade pip
}

Write-Host "Ensuring backend dependencies in .venv ..." -ForegroundColor Cyan
& $VenvPython -m pip install -q -r (Join-Path $Root "backend\requirements.txt")

$FrontendEnv = Join-Path $Root "frontend\.env"
if (-not (Test-Path $FrontendEnv)) {
    $Example = Join-Path $Root "frontend\.env.example"
    if (Test-Path $Example) {
        Copy-Item $Example $FrontendEnv
        Write-Host "Created frontend\.env from .env.example" -ForegroundColor Yellow
    } else {
        Set-Content $FrontendEnv "REACT_APP_API_URL=http://localhost:5001"
    }
}

# Always prefer local Flask while developing
$envLines = @(Get-Content $FrontendEnv -ErrorAction SilentlyContinue)
$envLines = $envLines | Where-Object { $_ -notmatch '^\s*REACT_APP_API_URL\s*=' }
$envLines += "REACT_APP_API_URL=http://localhost:5001"
Set-Content -Path $FrontendEnv -Value ($envLines -join "`n") -Encoding utf8
Write-Host "frontend\.env -> REACT_APP_API_URL=http://localhost:5001" -ForegroundColor Cyan

$backendCmd = @"
Set-Location '$Root\backend'
& '$VenvPython' app.py
"@

$frontendCmd = @"
Set-Location '$Root\frontend'
npm run dev
"@

Write-Host "Opening backend (Flask :5001) in a new window ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $backendCmd
)

Start-Sleep -Seconds 2

Write-Host "Opening frontend (npm run dev :3000) in a new window ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $frontendCmd
)

Write-Host ""
Write-Host "FRA Atlas is starting in two windows:" -ForegroundColor Cyan
Write-Host "  Frontend  http://localhost:3000"
Write-Host "  Backend   http://localhost:5001/api/health"
Write-Host "  Claims    http://localhost:3000/claims-data  (synthetic + Firestore)"
Write-Host "  DSS       http://localhost:3000/dss"
Write-Host ""
Write-Host "Close those windows (or Ctrl+C in each) to stop." -ForegroundColor Yellow
