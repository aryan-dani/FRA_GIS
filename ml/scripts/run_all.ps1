param(
  [ValidateSet("fast", "full")]
  [string]$Mode = "fast",
  [switch]$P0Only
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
  Write-Host "Venv missing. Run scripts/setup.ps1 first."
  exit 1
}
$args = @("-m", "fra_dss.cli", "run-all", "--mode", $Mode)
if ($P0Only) { $args += "--p0-only" }
& $Python @args
