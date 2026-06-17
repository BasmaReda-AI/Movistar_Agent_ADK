<#
.SYNOPSIS
    One-click launcher for the ElevenLabs + ADK Integration Demo.
    Starts ngrok, the Speech Engine server, and the FastAPI UI automatically.

    Usage: .\run_demo.ps1
    Stop:   .\cleanup.ps1
#>

$ProjectDir = "C:\Users\Peter\Downloads\personal-assistant\expermints\software-development-team\projects\Elevenlabs\ADK-Migration\elevenlabs_integration"
$LogDir = "$env:TEMP\elevenlabs-adk-demo"
$Null = New-Item -ItemType Directory -Path $LogDir -Force
$PidFile = "$LogDir\demo-pids.txt"

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

# 2. Start ngrok
Write-Status "  Starting ngrok tunnel..." -Color Yellow
$ngrokProcess = Start-Process -WindowStyle Hidden -FilePath "ngrok" `
    -ArgumentList "http", "3001" `
    -PassThru -WorkingDirectory $ProjectDir
Save-Pid "ngrok" $ngrokProcess.Id
Start-Sleep -Seconds 4

# 3. Get ngrok URL (retry up to 15 seconds)
Write-Status "  Getting ngrok public URL..." -Color Yellow
$ngrokUrl = $null
for ($i = 0; $i -lt 15; $i++) {
    try {
        $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop
        $ngrokUrl = $tunnels.tunnels[0].public_url
        if ($ngrokUrl) { break }
    } catch {
        # ngrok API not ready yet
    }
    Start-Sleep -Seconds 1
}

if (-not $ngrokUrl) {
    Write-Status "  [FAIL] Could not get ngrok URL." -Color Red
    Write-Status "     Is ngrok installed? Try running 'ngrok http 3001' manually." -Color Red
    Stop-Process -Id $ngrokProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Status "  [OK] ngrok URL: $ngrokUrl" -Color Green

# 4. Start Speech Engine server
Write-Status "  Starting Speech Engine server..." -Color Yellow
$engineLog = "$LogDir\engine.log"
$engineErrLog = "$LogDir\engine-err.log"
$engineProcess = Start-Process -WindowStyle Hidden -FilePath "python" `
    -ArgumentList "speech_engine_server.py", "--url", $ngrokUrl `
    -PassThru -WorkingDirectory $ProjectDir `
    -RedirectStandardOutput $engineLog -RedirectStandardError $engineErrLog
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
$apiProcess = Start-Process -WindowStyle Hidden -FilePath "python" `
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
