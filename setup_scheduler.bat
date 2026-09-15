@echo off
:: setup_scheduler.bat
:: Automatically registers a Windows Task Scheduler task to run the bot on LAPTOP STARTUP / LOGON + Daily at 09:00 AM

SET TASK_NAME=NaukriDailyAutoApply
SET SCRIPT_DIR=%~dp0
SET PS_SCRIPT=%SCRIPT_DIR%RunDailyNaukri.ps1

echo Setting up Windows Task Scheduler for Laptop Startup & Daily Execution...
echo Task Name: %TASK_NAME%
echo Trigger: On User Logon / Laptop Startup + Daily at 09:00 AM

:: Create Logon / Startup Trigger Task
schtasks /create /tn "%TASK_NAME%" /tr "powershell.exe -ExecutionPolicy Bypass -File \"%PS_SCRIPT%\"" /sc ONLOGON /f

:: Create Daily Backup Scheduled Task
schtasks /create /tn "%TASK_NAME%_Daily" /tr "powershell.exe -ExecutionPolicy Bypass -File \"%PS_SCRIPT%\"" /sc daily /st 09:00 /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Tasks '%TASK_NAME%' registered successfully in Windows Task Scheduler!
    echo The bot will now run automatically whenever you turn on/log into your laptop and every morning at 09:00 AM!
) else (
    echo.
    echo [ERROR] Failed to register task. Please try running this batch script as Administrator.
)

pause
