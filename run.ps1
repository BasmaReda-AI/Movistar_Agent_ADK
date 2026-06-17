$ErrorActionPreference = "Stop"
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ScriptPath

Write-Host "=== ADK + LiteLLM POC ===" -ForegroundColor Cyan

# 1. Create virtual environment if missing
if (-not (Test-Path -LiteralPath ".venv")) {
    Write-Host "[1/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# 2. Install requirements
Write-Host "[2/4] Installing dependencies..." -ForegroundColor Yellow
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Check .env exists
if (-not (Test-Path -LiteralPath ".env")) {
    Write-Host "[3/4] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "  .env created from .env.example — credentials are already set." -ForegroundColor Green
    pause
    exit
}

# 4. Launch web UI
Write-Host "[4/4] Launching web UI..." -ForegroundColor Green
Write-Host ""
Write-Host "  Web UI will open at http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "  Press Ctrl+C in this window to stop the server." -ForegroundColor Cyan
Write-Host ""

adk web
