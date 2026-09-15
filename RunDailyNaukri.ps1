# RunDailyNaukri.ps1
# PowerShell runner script for daily automated execution via Windows Task Scheduler

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $ScriptDir

$LogFile = Join-Path $ScriptDir "logs\daily_run.log"
if (-not (Test-Path -Path "$ScriptDir\logs")) {
    New-Item -ItemType Directory -Path "$ScriptDir\logs" | Out-Null
}

$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "=================================================="
Add-Content -Path $LogFile -Value "[$Timestamp] Starting daily Naukri auto-apply run..."

# Run bot script in headless mode
try {
    & python "$ScriptDir\bot.py" --headless >> $LogFile 2>&1
    Add-Content -Path $LogFile -Value "[$Timestamp] Daily run completed successfully."
    
    # Auto generate HTML report
    & python "$ScriptDir\reporter.py" >> $LogFile 2>&1
} catch {
    Add-Content -Path $LogFile -Value "[$Timestamp] ERROR during daily run: $_"
}
