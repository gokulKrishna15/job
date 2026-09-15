# Open-Report.ps1
# Refreshes and opens the latest HTML report in your browser
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $ScriptDir

& python "$ScriptDir\reporter.py"
Invoke-Item "$ScriptDir\reports\latest_report.html"
