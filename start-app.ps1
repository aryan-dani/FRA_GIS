# FRA Atlas — one-command local stack (React + Flask API).
# Usage (from repo root):
#   .\start-app.ps1
#
# Note: the API is Flask (backend/app.py on :5001), not FastAPI.
# Frees ports 3000/3001/5001, ensures .venv + deps, then opens two windows.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Stop-PortListeners {
    param([int[]]$Ports)
    foreach ($port in $Ports) {
        try {
            $pids = @(
                Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
                    Select-Object -ExpandProperty OwningProcess -Unique
            ) | Where-Object { $_ -and $_ -ne 0 }
            foreach ($procId in $pids) {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "Killing $($proc.ProcessName) (PID $procId) on :$port ..." -ForegroundColor Yellow
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                }
            }
        } catch {
            # port may already be free
        }
    }
    Start-Sleep -Seconds 1
}

Write-Host "==> FRA Atlas local start" -ForegroundColor Cyan
Write-Host "Clearing ports 3000, 3001, 5001 ..." -ForegroundColor Cyan
Stop-PortListeners -Ports @(3000, 3001, 5001)

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating .venv ..." -ForegroundColor Cyan
    python -m venv .venv
    & $VenvPython -m pip install --upgrade pip
}

Write-Host "Ensuring Flask API deps in .venv ..." -ForegroundColor Cyan
& $VenvPython -m pip install -q -r (Join-Path $Root "backend\requirements.txt")
# So ETA / rejection-reason joblibs can unpickle fra_dss pipelines
& $VenvPython -m pip install -q -e (Join-Path $Root "ml") --no-deps

$FrontendEnv = Join-Path $Root "frontend\.env"
$FrontendEnvDev = Join-Path $Root "frontend\.env.development"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Upsert-EnvFile {
    param([string]$Path, [hashtable]$Pairs)
    $map = @{}
    if (Test-Path $Path) {
        Get-Content $Path -Encoding UTF8 | ForEach-Object {
            $line = $_.TrimStart([char]0xFEFF)
            if ($line -match '^\s*([^#=]+)=(.*)$') {
                $map[$Matches[1].Trim()] = $Matches[2].Trim()
            }
        }
    }
    foreach ($k in $Pairs.Keys) { $map[$k] = $Pairs[$k] }
    $lines = @()
    foreach ($k in ($map.Keys | Sort-Object)) {
        $lines += "$k=$($map[$k])"
    }
    [System.IO.File]::WriteAllLines($Path, $lines, $utf8NoBom)
}

$existingMapsKey = ""
if (Test-Path $FrontendEnv) {
    $m = Select-String -Path $FrontendEnv -Pattern '^\s*REACT_APP_GOOGLE_MAPS_API_KEY\s*=(.*)$' | Select-Object -First 1
    if ($m) {
        $existingMapsKey = $m.Matches[0].Groups[1].Value.Trim().TrimStart([char]0xFEFF)
    }
}

if (-not (Test-Path $FrontendEnv)) {
    $Example = Join-Path $Root "frontend\.env.example"
    if (Test-Path $Example) { Copy-Item $Example $FrontendEnv }
}

Upsert-EnvFile -Path $FrontendEnv -Pairs @{ "REACT_APP_API_URL" = "http://localhost:5001" }
$devPairs = @{ "REACT_APP_API_URL" = "http://localhost:5001" }
if ($existingMapsKey) { $devPairs["REACT_APP_GOOGLE_MAPS_API_KEY"] = $existingMapsKey }
Upsert-EnvFile -Path $FrontendEnvDev -Pairs $devPairs
Write-Host "frontend env -> REACT_APP_API_URL=http://localhost:5001" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $Root "frontend\node_modules"))) {
    Write-Host "Installing frontend npm packages (first run) ..." -ForegroundColor Cyan
    Push-Location (Join-Path $Root "frontend")
    try { npm install } finally { Pop-Location }
}

$modelPath = Join-Path $Root "backend\models\claim_outcome.joblib"
if (-not (Test-Path $modelPath)) {
    Write-Host "WARNING: claim_outcome.joblib missing — DSS predict will 503 until you train." -ForegroundColor Yellow
}

$backendCmd = @"
`$Host.UI.RawUI.WindowTitle = 'FRA Atlas API (Flask) :5001'
Set-Location '$Root\backend'
Write-Host 'Flask API starting on http://127.0.0.1:5001 ...' -ForegroundColor Green
& '$VenvPython' app.py
"@

$frontendCmd = @"
`$Host.UI.RawUI.WindowTitle = 'FRA Atlas React :3000'
Set-Location '$Root\frontend'
`$env:PORT = '3000'
`$env:BROWSER = 'none'
`$env:NODE_OPTIONS = '--no-deprecation'
Write-Host 'React starting on http://localhost:3000 ...' -ForegroundColor Green
npm run dev
"@

Write-Host "Opening Flask API (:5001) ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $backendCmd
)

Start-Sleep -Seconds 2

Write-Host "Opening React CRA (:3000) ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $frontendCmd
)

# Open DSS once the SPA is likely up (HashRouter)
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 12
    Start-Process "http://localhost:3000/#/dss"
} | Out-Null

Write-Host ""
Write-Host "FRA Atlas is starting:" -ForegroundColor Cyan
Write-Host "  React     http://localhost:3000"
Write-Host "  Flask API http://localhost:5001/api/health"
Write-Host "  DSS       http://localhost:3000/#/dss"
Write-Host "  Claims    http://localhost:3000/#/claims-data"
Write-Host ""
Write-Host "Close the two PowerShell windows (or Ctrl+C in each) to stop." -ForegroundColor Yellow
