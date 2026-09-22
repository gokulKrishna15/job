import os
import csv
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
REPORT_DIR = BASE_DIR / "reports"
HISTORY_FILE = LOG_DIR / "application_history.csv"
SKIPPED_FILE = LOG_DIR / "skipped_jobs.csv"
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def calculate_match_score(title, company, user_skills):
    title_lower = title.lower()
    score = 70  # base match for appearing in search
    matched_tags = []
    
    keywords_map = {
        "devops": ("DevOps", 15),
        "fastapi": ("FastAPI", 15),
        "python": ("Python", 10),
        "backend": ("Backend", 10),
        "platform": ("Platform", 15),
        "full stack": ("FullStack", 10),
        "fullstack": ("FullStack", 10),
        "software engineer": ("Software Eng", 10),
        "postgres": ("PostgreSQL", 10),
        "docker": ("Docker", 10),
        "ci/cd": ("CI/CD", 10),
        "aws": ("AWS", 5),
        "linux": ("Linux", 5)
    }
    
    for kw, (tag, points) in keywords_map.items():
        if kw in title_lower:
            score += points
            matched_tags.append(tag)
            
    score = min(score, 98)
    return score, matched_tags

def generate_report():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_config()
    profile = config.get("user_profile", {})
    candidate_name = profile.get("name", "S Gokul Krishna")
    candidate_headline = profile.get("headline", "DevOps Engineer & Backend Developer")

    today_str = datetime.now().strftime("%Y-%m-%d")
    now_formatted = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    
    applied_today = []
    external_high_matches = []
    skipped_other = []

    # Parse application history (strict today filter)
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row or len(row) < 6:
                    continue
                timestamp, title, company, location, url, status = row[:6]
                if timestamp.startswith(today_str):
                    applied_today.append({
                        "time": timestamp,
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": url,
                        "status": status
                    })

    # Parse skipped external jobs for intelligent recommendations (strict today filter)
    if SKIPPED_FILE.exists():
        with open(SKIPPED_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row or len(row) < 5:
                    continue
                timestamp, title, company, url, reason = row[:5]
                if not timestamp.startswith(today_str):
                    continue
                    
                score, tags = calculate_match_score(title, company, profile.get("skills", []))
                
                job_obj = {
                    "time": timestamp,
                    "title": title,
                    "company": company,
                    "url": url,
                    "reason": reason,
                    "score": score,
                    "tags": tags
                }
                
                if "External" in reason and score >= 75:
                    external_high_matches.append(job_obj)
                else:
                    skipped_other.append(job_obj)

    # Sort external matches by score descending
    external_high_matches.sort(key=lambda x: x["score"], reverse=True)

    # Breakdown by category
    category_counts = {"DevOps": 0, "Backend": 0, "FastAPI": 0, "Python": 0, "Platform/FullStack": 0, "Software Eng": 0}
    for item in applied_today:
        t_low = item["title"].lower()
        if "devops" in t_low:
            category_counts["DevOps"] += 1
        elif "fastapi" in t_low:
            category_counts["FastAPI"] += 1
        elif "backend" in t_low:
            category_counts["Backend"] += 1
        elif "python" in t_low:
            category_counts["Python"] += 1
        elif "platform" in t_low or "full" in t_low:
            category_counts["Platform/FullStack"] += 1
        else:
            category_counts["Software Eng"] += 1

    # 1. Generate Markdown Report
    md_path = REPORT_DIR / f"report_{today_str}.md"
    latest_md = REPORT_DIR / "latest_report.md"

    md_content = f"""# 📊 Daily Naukri Automation & Job Intelligence Report
**Date**: {now_formatted}  
**Candidate**: {candidate_name} ({candidate_headline})

---

## 📈 Executive Summary

- **Total Jobs Auto-Applied Today**: `{len(applied_today)}`
- **Recommended High-Match External Jobs**: `{len(external_high_matches)}`
- **Profile Status**: `Active Today (Headline Refreshed)`

### Category Distribution
- **DevOps Roles**: {category_counts['DevOps']}
- **Backend Developer Roles**: {category_counts['Backend']}
- **FastAPI Developer Roles**: {category_counts['FastAPI']}
- **Python Developer Roles**: {category_counts['Python']}
- **Platform & Full Stack Roles**: {category_counts['Platform/FullStack']}
- **Software Engineering Roles**: {category_counts['Software Eng']}

---

## 🌟 High-Priority External Jobs (Manual Apply Recommended)
*These jobs require external ATS application (e.g. Workday/Company Portal) and are scored as strong matches for your DevOps & Backend stack:*

| Match Score | Job Title | Company | Skills / Tags | Direct Link |
| :---: | :--- | :--- | :--- | :--- |
"""
    for job in external_high_matches[:15]:
        tags_str = ", ".join(job["tags"]) if job["tags"] else "Backend / DevOps"
        md_content += f"| **{job['score']}%** | {job['title']} | {job['company']} | `{tags_str}` | [Apply Now 🔗]({job['url']}) |\n"

    if not external_high_matches:
        md_content += "| - | No high-match external jobs flagged today | - | - | - |\n"

    md_content += f"""
---

## 🤖 Auto-Applied Naukri Jobs ({len(applied_today)})

| Time | Job Title | Company | Location | Status | Link |
| :--- | :--- | :--- | :--- | :---: | :--- |
"""
    for job in applied_today[:25]:
        md_content += f"| {job['time'].split()[-1]} | {job['title']} | {job['company']} | {job['location']} | `{job['status']}` | [View 🔗]({job['url']}) |\n"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    with open(latest_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 2. Generate Interactive Dark-Mode HTML Report
    html_path = REPORT_DIR / f"report_{today_str}.html"
    latest_html = REPORT_DIR / "latest_report.html"

    ext_rows_html = ""
    for job in external_high_matches[:20]:
        tags_html = "".join([f'<span class="tag">{t}</span>' for t in job['tags']]) or '<span class="tag">Backend</span>'
        ext_rows_html += f"""
        <tr>
            <td><span class="badge score-high">{job['score']}% Match</span></td>
            <td><strong>{job['title']}</strong></td>
            <td>{job['company']}</td>
            <td>{tags_html}</td>
            <td><a href="{job['url']}" target="_blank" class="btn btn-apply">Apply on Company Site ↗</a></td>
        </tr>
        """
    if not ext_rows_html:
        ext_rows_html = "<tr><td colspan='5' style='text-align:center; padding:20px;'>No high-match external jobs flagged for today.</td></tr>"

    applied_rows_html = ""
    for job in applied_today[:30]:
        status_class = "badge-success" if "APPLIED" in job['status'] else "badge-info"
        applied_rows_html += f"""
        <tr>
            <td style="font-size: 0.85rem; color: #94a3b8;">{job['time']}</td>
            <td><strong>{job['title']}</strong></td>
            <td>{job['company']}</td>
            <td>{job['location']}</td>
            <td><span class="badge {status_class}">{job['status']}</span></td>
            <td><a href="{job['url']}" target="_blank" class="btn btn-secondary">View Job ↗</a></td>
        </tr>
        """
    if not applied_rows_html:
        applied_rows_html = "<tr><td colspan='6' style='text-align:center; padding:20px;'>No auto-applied jobs recorded for today yet.</td></tr>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Naukri Automation Dashboard - {candidate_name}</title>

    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border-color: rgba(255, 255, 255, 0.1);
            --primary: #38bdf8;
            --accent: #818cf8;
            --success: #34d399;
            --warning: #fbbf24;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 30px;
            background-image: radial-gradient(circle at 10% 20%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
                              radial-gradient(circle at 90% 80%, rgba(129, 140, 248, 0.08) 0%, transparent 40%);
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 25px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 30px;
        }}
        h1 {{
            font-size: 1.8rem;
            margin: 0;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            color: var(--text-sub);
            font-size: 0.95rem;
            margin-top: 5px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 35px;
        }}
        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        }}
        .stat-value {{
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--primary);
            margin-top: 10px;
        }}
        .stat-label {{
            font-size: 0.85rem;
            color: var(--text-sub);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .section-title {{
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .table-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 40px;
            backdrop-filter: blur(12px);
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th, td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            color: var(--text-sub);
            font-size: 0.85rem;
            text-transform: uppercase;
            font-weight: 600;
        }}
        tr:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 600;
        }}
        .score-high {{
            background: rgba(52, 211, 153, 0.2);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.3);
        }}
        .badge-success {{
            background: rgba(56, 189, 248, 0.2);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }}
        .badge-info {{
            background: rgba(129, 140, 248, 0.2);
            color: #818cf8;
        }}
        .tag {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.08);
            color: #cbd5e1;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            margin-right: 4px;
        }}
        .btn {{
            display: inline-block;
            padding: 7px 14px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.82rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        .btn-apply {{
            background: linear-gradient(135deg, #38bdf8, #0284c7);
            color: #ffffff;
        }}
        .btn-apply:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
        }}
        .btn-secondary {{
            background: rgba(255, 255, 255, 0.1);
            color: #f1f5f9;
        }}
        .btn-secondary:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Naukri Job Intelligence & Automation Dashboard</h1>
                <div class="subtitle">Candidate: <strong>{candidate_name}</strong> | {candidate_headline}</div>
            </div>
            <div style="text-align: right;">
                <div style="background: rgba(52, 211, 153, 0.15); border: 1px solid rgba(52, 211, 153, 0.3); color: #34d399; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; margin-bottom: 6px;">
                    <span style="width: 8px; height: 8px; background: #34d399; border-radius: 50%; display: inline-block;"></span> LIVE REFRESHED: {now_formatted}
                </div>
            </div>
        </header>


        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Auto-Applied Today</div>
                <div class="stat-value">{len(applied_today)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Recommended External Jobs</div>
                <div class="stat-value" style="color: var(--accent);">{len(external_high_matches)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Profile Visibility Status</div>
                <div class="stat-value" style="color: var(--success); font-size: 1.3rem; margin-top: 15px;">🟢 Active Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">DevOps & Backend Ratio</div>
                <div class="stat-value" style="font-size: 1.4rem; color: #f472b6; margin-top: 15px;">
                    {category_counts['DevOps']} DevOps / {category_counts['Backend'] + category_counts['FastAPI'] + category_counts['Python']} Backend
                </div>
            </div>
        </div>

        <div class="section-title">🌟 High-Priority External Jobs (Manual Apply Recommended)</div>
        <div class="table-card">
            <table>
                <thead>
                    <tr>
                        <th>Match Score</th>
                        <th>Job Title</th>
                        <th>Company</th>
                        <th>Skill Tags</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {ext_rows_html}
                </tbody>
            </table>
        </div>

        <div class="section-title">🤖 Today's Auto-Applied Naukri Jobs</div>
        <div class="table-card">
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Job Title</th>
                        <th>Company</th>
                        <th>Location</th>
                        <th>Status</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
                    {applied_rows_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(latest_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n[REPORT GENERATED] Intelligent Dashboard generated successfully:")
    print(f"--> HTML Report: {latest_html}")
    print(f"--> Markdown Summary: {latest_md}")

if __name__ == "__main__":
    generate_report()
