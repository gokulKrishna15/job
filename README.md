# Daily Automated Naukri Job Applicator & Profile Booster

An automated tool designed for **S Gokul Krishna** to update his Naukri profile daily (boosting recruiter visibility) and automatically apply for **DevOps Engineer**, **Backend Developer**, **FastAPI**, and **Python Developer** jobs in **Bengaluru** and **Remote** locations.

---

## Features

1. **Daily Profile Booster**: Touches and updates your profile headline daily so recruiters see your profile listed as **"Active Today"** (significantly increases profile views).
2. **Persistent Login Session**: Interactive initial login that saves session cookies (`auth/storage_state.json`), enabling fully automated daily background runs without repeating login/OTP prompts.
3. **Smart Job Applicator**: Automatically searches job listings, filters relevant roles, handles 1-click applications, and skips external questionnaires/company redirects safely.
4. **Audit History & Logs**: Logs all applied jobs to `logs/application_history.csv` and skipped jobs to `logs/skipped_jobs.csv`.
5. **Windows Task Scheduler Ready**: Pre-configured PowerShell and `.bat` setup scripts to run automatically every day at 09:00 AM.

---

## Quick Start Guide

### Step 1: Install Dependencies
Open your terminal in this folder (`C:\Users\Lumbini_User\.gemini\antigravity\scratch\naukri-auto-apply`) and run:
```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 2: One-Time Interactive Login
Run the interactive login script to open a browser window:
```bash
python login.py
```
- Enter your Naukri email/password and complete OTP/CAPTCHA if prompted.
- Once you reach the main dashboard/profile, press **ENTER** in your terminal.
- Your session is saved to `auth/storage_state.json`.

### Step 3: Test the Bot (Dry Run)
Test your setup without sending live job applications:
```bash
python bot.py --dry-run
```

### Step 4: Run Live Application Manual Test
To perform a live run:
```bash
python bot.py
```

### Step 5: Enable Automated Daily Execution
To schedule the bot to run automatically every day at 9:00 AM:
- Right-click `setup_scheduler.bat` -> **Run as Administrator**.
- Or run in terminal:
```cmd
setup_scheduler.bat
```

---

## Settings & Preferences (`config.json`)

You can edit `config.json` at any time to update search terms or application limits:

```json
{
  "user_profile": {
    "name": "S Gokul Krishna",
    "headline": "DevOps Engineer & Backend Developer (Python / FastAPI / PostgreSQL)"
  },
  "keywords": [
    "DevOps Engineer",
    "Backend Developer",
    "FastAPI Developer",
    "Python Developer",
    "DevOps"
  ],
  "locations": ["Bengaluru", "Bangalore", "Remote"],
  "experience_years": 2,
  "daily_apply_limit": 25
}
```

---

## Application Logs & Audits

- **`logs/application_history.csv`**: Contains timestamps, job titles, company names, job URLs, and status (`APPLIED` / `ALREADY_APPLIED`).
- **`logs/skipped_jobs.csv`**: Records jobs that required custom external applications or detailed questionnaires so you can manually review them if needed.
- **`logs/daily_run.log`**: Output logs generated during automated daily Task Scheduler runs.
