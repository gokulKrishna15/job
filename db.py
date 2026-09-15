import sqlite3
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "naukri_tracker.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: Job Applications Tracked
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_url TEXT UNIQUE,
        title TEXT,
        company TEXT,
        location TEXT,
        applied_at DATETIME,
        status TEXT, -- APPLIED, DRY_RUN_APPLIED, ALREADY_APPLIED, INTERVIEW, OFFER, REJECTED
        notes TEXT
    )
    """)

    # Table 2: Skipped / External High Match Jobs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS external_opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_url TEXT UNIQUE,
        title TEXT,
        company TEXT,
        discovered_at DATETIME,
        match_score INTEGER,
        skill_tags TEXT,
        reason TEXT,
        status TEXT DEFAULT 'PENDING' -- PENDING, APPLIED_MANUALLY, IGNORED
    )
    """)

    # Table 3: Daily Summary Analytics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_analytics (
        date TEXT PRIMARY KEY,
        auto_applied_count INTEGER,
        external_high_match_count INTEGER,
        profile_boosted INTEGER,
        last_updated DATETIME
    )
    """)

    conn.commit()
    conn.close()

def save_application_db(title, company, location, url, status):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO applications (job_url, title, company, location, applied_at, status)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(job_url) DO UPDATE SET
        status = excluded.status,
        applied_at = excluded.applied_at
    """, (url, title, company, location, now_str, status))

    conn.commit()
    conn.close()

def save_external_job_db(title, company, url, match_score, tags, reason):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO external_opportunities (job_url, title, company, discovered_at, match_score, skill_tags, reason)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(job_url) DO UPDATE SET
        match_score = excluded.match_score,
        discovered_at = excluded.discovered_at
    """, (url, title, company, now_str, match_score, json.dumps(tags), reason))

    conn.commit()
    conn.close()

def get_today_analytics_db():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    today_prefix = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("SELECT COUNT(*) as cnt FROM applications WHERE datetime(applied_at) >= datetime(?)", (today_prefix + " 00:00:00",))
    applied_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM external_opportunities WHERE datetime(discovered_at) >= datetime(?) AND match_score >= 75", (today_prefix + " 00:00:00",))
    external_count = cursor.fetchone()["cnt"]

    conn.close()
    return {
        "today_applied": applied_count,
        "today_external": external_count
    }

if __name__ == "__main__":
    init_db()
    print(f"[DB SUCCESS] SQLite Database initialized at: {DB_FILE}")
