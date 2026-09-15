@echo off
:: open_report.bat - Refreshes and opens the latest HTML report in your browser
cd /d "%~dp0"
python reporter.py
start "" "reports\latest_report.html"
