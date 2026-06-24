<#
.SYNOPSIS
    Stops the ElevenLabs + ADK Integration Demo and cleans up.
    Run this after you're done with the demo.

    Usage: .\cleanup.ps1
#>

$LogDir = "$env:TEMP\elevenlabs-adk-demo"
$PidFile = "$LogDir\demo-pids.txt"
$ProjectDir = "C:\Users\Peter\Downloads\personal-assistant\expermints\software-development-team\projects\Elevenlabs\ADK-Migration\elevenlabs_integration"

Write-Host ""
Write-Host "+----------------------------------------------+" -ForegroundColor Yellow
Write-Host "|     Cleaning up Demo                         |" -ForegroundColor Yellow
Write-Host "+----------------------------------------------+" -ForegroundColor Yellow
Write-Host ""

$stoppedSomething = $false

# Stop processes by saved PIDs
if (Test-Path $PidFile) {
    Get-Content $PidFile | ForEach-Object {
        $parts = $_ -split "="
        if ($parts.Count -eq 2) {
            $name = $parts[0]
            $pidNum = [int]$parts[1]
            $proc = Get-Process -Id $pidNum -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $pidNum -Force -ErrorAction SilentlyContinue
                Write-Host "  [OK] Stopped $name (PID $pidNum)" -ForegroundColor Green
                $stoppedSomething = $true
            } else {
                Write-Host "  [--] $name (PID $pidNum) was already stopped" -ForegroundColor Gray
            }
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

# Cleanup .engine_id and voice_context files
Remove-Item "$ProjectDir\.engine_id" -Force -ErrorAction SilentlyContinue
Remove-Item "$ProjectDir\voice_context.json" -Force -ErrorAction SilentlyContinue
Remove-Item "$ProjectDir\voice_transcript.json" -Force -ErrorAction SilentlyContinue

# Final check: kill any orphaned cloudflared processes
$orphanCf = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($orphanCf) {
    $orphanCf | Stop-Process -Force
    Write-Host "  [OK] Stopped orphaned cloudflared process" -ForegroundColor Green
    $stoppedSomething = $true
}

# Remove temp logs
Remove-Item "$LogDir\*.log" -Force -ErrorAction SilentlyContinue

if (-not $stoppedSomething) {
    Write-Host "  [--] Nothing was running. All clean!" -ForegroundColor Gray
}

Write-Host ""
Write-Host "  Cleanup complete!" -ForegroundColor Cyan
Write-Host ""
