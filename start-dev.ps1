# Start FRA Atlas frontend + backend together (Windows PowerShell).
# Usage (from repo root):
#   .\start-dev.ps1
#
# Always frees ports 3000/3001/5001 first, then starts Flask + CRA.

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
                    Write-Host "Killing $($proc.ProcessName) (PID $procId) on port $port ..." -ForegroundColor Yellow
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                }
            }
        } catch {
            # ignore — port may already be free
        }
    }
    Start-Sleep -Seconds 1
}

Write-Host "Clearing ports 3000, 3001, 5001 ..." -ForegroundColor Cyan
Stop-PortListeners -Ports @(3000, 3001, 5001)

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating .venv ..." -ForegroundColor Cyan
    python -m venv .venv
    & $VenvPython -m pip install --upgrade pip
}

Write-Host "Ensuring backend dependencies in .venv ..." -ForegroundColor Cyan
& $VenvPython -m pip install -q -r (Join-Path $Root "backend\requirements.txt")

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

# Preserve existing Maps key if present
$existingMapsKey = ""
if (Test-Path $FrontendEnv) {
    $m = Select-String -Path $FrontendEnv -Pattern '^\s*REACT_APP_GOOGLE_MAPS_API_KEY\s*=(.*)$' | Select-Object -First 1
    if ($m) { $existingMapsKey = $m.Matches[0].Groups[1].Value.Trim().TrimStart([char]0xFEFF) }
}

$envPairs = @{
    "REACT_APP_API_URL" = "http://localhost:5001"
}
if ($existingMapsKey) {
    $envPairs["REACT_APP_GOOGLE_MAPS_API_KEY"] = $existingMapsKey
} elseif (Test-Path $FrontendEnv) {
    # keep other keys from file via Upsert by reading full file first — already in map
}

# Seed from existing .env so Firebase keys are not wiped
if (Test-Path $FrontendEnv) {
    Upsert-EnvFile -Path $FrontendEnv -Pairs @{ "REACT_APP_API_URL" = "http://localhost:5001" }
} else {
    $Example = Join-Path $Root "frontend\.env.example"
    if (Test-Path $Example) { Copy-Item $Example $FrontendEnv }
    Upsert-EnvFile -Path $FrontendEnv -Pairs @{ "REACT_APP_API_URL" = "http://localhost:5001" }
}

# CRA loads .env.development in npm run dev — keep API URL + maps key here too
$devPairs = @{ "REACT_APP_API_URL" = "http://localhost:5001" }
if ($existingMapsKey) { $devPairs["REACT_APP_GOOGLE_MAPS_API_KEY"] = $existingMapsKey }
Upsert-EnvFile -Path $FrontendEnvDev -Pairs $devPairs
Write-Host "frontend env -> REACT_APP_API_URL=http://localhost:5001 (UTF-8 no BOM)" -ForegroundColor Cyan

$backendCmd = @"
`$Host.UI.RawUI.WindowTitle = 'FRA Atlas API :5001'
Set-Location '$Root\backend'
& '$VenvPython' app.py
"@

$frontendCmd = @"
`$Host.UI.RawUI.WindowTitle = 'FRA Atlas Frontend :3000'
Set-Location '$Root\frontend'
`$env:PORT = '3000'
`$env:BROWSER = 'none'
`$env:NODE_OPTIONS = '--no-deprecation'
npm run dev
"@

Write-Host "Opening backend (Flask :5001) ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $backendCmd
)

Start-Sleep -Seconds 3

Write-Host "Opening frontend (CRA :3000) ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $frontendCmd
)

Write-Host ""
Write-Host "FRA Atlas is starting:" -ForegroundColor Cyan
Write-Host "  Frontend  http://localhost:3000"
Write-Host "  Backend   http://localhost:5001/api/health"
Write-Host "  Claims    http://localhost:3000/claims-data"
Write-Host "  DSS       http://localhost:3000/dss"
Write-Host ""
Write-Host "Close those windows (or Ctrl+C in each) to stop." -ForegroundColor Yellow
