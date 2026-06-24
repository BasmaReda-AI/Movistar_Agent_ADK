<#
.SYNOPSIS
    One-click launcher for the ElevenLabs + ADK Integration Demo.
    Starts a Cloudflare Tunnel, the Speech Engine server, and the FastAPI UI automatically.

    Usage: .\run_demo.ps1
    Stop:   .\cleanup.ps1
#>

$ProjectDir = "C:\Users\Peter\Downloads\personal-assistant\expermints\software-development-team\projects\Elevenlabs\ADK-Migration\elevenlabs_integration"
$LogDir = "$env:TEMP\elevenlabs-adk-demo"
$Null = New-Item -ItemType Directory -Path $LogDir -Force
$PidFile = "$LogDir\demo-pids.txt"

# Locate the correct Python interpreter (must have elevenlabs installed)
$PythonBin = (Get-Command "python" -ErrorAction SilentlyContinue).Source
if ($PythonBin) {
    # Verify it can import elevenlabs
    $test = & $PythonBin -c "import elevenlabs; print('OK')" 2>&1
    if ($test -ne "OK") { $PythonBin = $null }
}
if (-not $PythonBin) {
    # Fallback to known good paths
    $candidates = @(
        "C:\Users\Peter\AppData\Local\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            $test = & $c -c "import elevenlabs; print('OK')" 2>&1
            if ($test -eq "OK") { $PythonBin = $c; break }
        }
    }
}
if (-not $PythonBin) {
    Write-Host "  [FAIL] Could not find Python with elevenlabs installed." -ForegroundColor Red
    Write-Host "     Install with: pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}
Write-Host "  Using Python: $PythonBin" -ForegroundColor Gray

# -- Helper functions -------------------------------------------------

function Write-Status {
    param([string]$Text, [string]$Color = "White")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Text" -ForegroundColor $Color
}

function Save-Pid {
    param([string]$Name, [int]$ProcessId)
    Add-Content -Path $PidFile -Value "$Name=$ProcessId"
}

function Cleanup-OldProcesses {
    # Kill any leftover processes from previous runs
    if (Test-Path $PidFile) {
        Write-Status "  Cleaning up previous run..." -Color Yellow
        Get-Content $PidFile | ForEach-Object {
            $parts = $_ -split "="
            if ($parts.Count -eq 2) {
                $oldPid = [int]$parts[1]
                Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
                Write-Status "    Stopped $($parts[0]) (PID $oldPid)" -Color Gray
            }
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }
    Remove-Item "$ProjectDir\.engine_id" -Force -ErrorAction SilentlyContinue
}

# -- Start ------------------------------------------------------------

Write-Host ""
Write-Host "+----------------------------------------------+" -ForegroundColor Cyan
Write-Host "|  ElevenLabs + ADK Integration Demo           |" -ForegroundColor Cyan
Write-Host "+----------------------------------------------+" -ForegroundColor Cyan
Write-Host ""

# 1. Cleanup
Cleanup-OldProcesses

# 2. Start cloudflared tunnel
Write-Status "  Starting cloudflared tunnel..." -Color Yellow
$cfBin = (Get-Command "cloudflared" -ErrorAction SilentlyContinue).Source
if (-not $cfBin) {
    $cfBin = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
    if (-not (Test-Path $cfBin)) {
        Write-Status "  [FAIL] cloudflared not found. Install: winget install cloudflare.cloudflared" -Color Red
        exit 1
    }
}
$cfLog = "$LogDir\cloudflared.log"
$cfOutLog = "$LogDir\cloudflared-out.log"
$cfProcess = Start-Process -WindowStyle Hidden -FilePath $cfBin `
    -ArgumentList "tunnel", "--url", "http://localhost:3001" `
    -PassThru -WorkingDirectory $ProjectDir `
    -RedirectStandardError $cfLog -RedirectStandardOutput $cfOutLog
Save-Pid "cloudflared" $cfProcess.Id

# 3. Get tunnel URL (retry up to 20 seconds)
Write-Status "  Getting cloudflared public URL..." -Color Yellow
$tunnelUrl = $null
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $cfLog) {
        $content = Get-Content $cfLog -Raw -ErrorAction SilentlyContinue
        if ($content -match "(https://[a-zA-Z0-9\-]+\.trycloudflare\.com)") {
            $tunnelUrl = $matches[1]
            break
        }
    }
    if ($cfProcess.HasExited) {
        Write-Status "  cloudflared process exited unexpectedly." -Color Red
        Get-Content $cfLog -Tail 10 | ForEach-Object { Write-Host "     $_" -ForegroundColor Red }
        break
    }
}

if (-not $tunnelUrl) {
    Write-Status "  [FAIL] Could not get cloudflared tunnel URL." -Color Red
    Write-Status "     Is cloudflared installed? Try: winget install cloudflare.cloudflared" -Color Red
    Write-Status "     Or run manually: cloudflared tunnel --url http://localhost:3001" -Color Red
    Get-Content $cfLog -Tail 10 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "     $_" -ForegroundColor Red }
    Stop-Process -Id $cfProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Status "  [OK] Tunnel URL: $tunnelUrl" -Color Green

# 4. Start Speech Engine server
Write-Status "  Starting Speech Engine server..." -Color Yellow
$engineLog = "$LogDir\engine.log"
$engineErrLog = "$LogDir\engine-err.log"
$engineProcess = Start-Process -WindowStyle Hidden -FilePath $PythonBin `
    -ArgumentList "speech_engine_server.py", "--url", $tunnelUrl `
    -PassThru -WorkingDirectory $ProjectDir
Save-Pid "engine" $engineProcess.Id

# 5. Wait for Speech Engine to be created (checks for .engine_id file, up to 30s)
Write-Status "  Waiting for Speech Engine creation..." -Color Yellow
$engineIdFile = "$ProjectDir\.engine_id"
$created = $false
for ($i = 0; $i -lt 30; $i++) {
    if (Test-Path $engineIdFile) {
        $engineId = Get-Content $engineIdFile
        Write-Status "  [OK] Speech Engine created! ID: $engineId" -Color Green
        $created = $true
        break
    }
    # Check if process died
    if (-not $engineProcess.HasExited) {
        Start-Sleep -Seconds 1
    } else {
        Write-Status "  [FAIL] Engine process exited unexpectedly." -Color Red
        Get-Content $engineLog -Tail 10 | ForEach-Object { Write-Host "     $_" -ForegroundColor Red }
        Cleanup-OldProcesses
        exit 1
    }
}

if (-not $created) {
    Write-Status "  [FAIL] Timed out waiting for Speech Engine." -Color Red
    Get-Content $engineLog -Tail 10 | ForEach-Object { Write-Host "     $_" -ForegroundColor Red }
    Cleanup-OldProcesses
    exit 1
}

# 6. Start FastAPI server
Write-Status "  Starting FastAPI server..." -Color Yellow
$apiLog = "$LogDir\api.log"
$apiErrLog = "$LogDir\api-err.log"
$apiProcess = Start-Process -WindowStyle Hidden -FilePath $PythonBin `
    -ArgumentList "api.py" `
    -PassThru -WorkingDirectory $ProjectDir `
    -RedirectStandardOutput $apiLog -RedirectStandardError $apiErrLog
Save-Pid "api" $apiProcess.Id
Start-Sleep -Seconds 3

# 7. Open browser
Write-Status "  Opening browser..." -Color Yellow
Start-Process "http://localhost:8501"

# 8. Done!
Write-Host ""
Write-Host "+----------------------------------------------+" -ForegroundColor Green
Write-Host "|     Demo is up and running!                  |" -ForegroundColor Green
Write-Host "+----------------------------------------------+" -ForegroundColor Green
Write-Host "|                                              |" -ForegroundColor Green
Write-Host "|  Browser should open at:                     |" -ForegroundColor Green
Write-Host "|     http://localhost:8501                    |" -ForegroundColor Green
Write-Host "|                                              |" -ForegroundColor Green
Write-Host "|  To stop everything, run:                    |" -ForegroundColor Green
Write-Host "|     .\cleanup.ps1                            |" -ForegroundColor Green
Write-Host "|                                              |" -ForegroundColor Green
Write-Host "+----------------------------------------------+" -ForegroundColor Green
Write-Host ""
