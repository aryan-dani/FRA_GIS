# FRA DSS ML setup (Windows PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Py = if (Get-Command py -ErrorAction SilentlyContinue) { "py -3.11" } else { "python" }
Write-Host "Creating venv at ml/.venv ..."
& $Py -m venv .venv
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

& $Python -m pip install --upgrade pip
& $Pip install -r requirements.txt
& $Pip install -e .
& $Python -m ipykernel install --user --name fra-dss --display-name "Python (fra-dss)"
Write-Host "Setup complete. Activate: .\ml\.venv\Scripts\Activate.ps1"
