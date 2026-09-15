import os
import sys
import json
import time
import random
import csv
import argparse
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Force real-time log output for cloud runners
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

BASE_DIR = Path(__file__).parent
AUTH_FILE = BASE_DIR / "auth" / "storage_state.json"
CONFIG_FILE = BASE_DIR / "config.json"
LOG_DIR = BASE_DIR / "logs"
HISTORY_FILE = LOG_DIR / "application_history.csv"
SKIPPED_FILE = LOG_DIR / "skipped_jobs.csv"

def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Configuration file missing: {CONFIG_FILE}")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def purge_previous_days_logs():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    archive_dir = LOG_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    today_prefix = datetime.now().strftime("%Y-%m-%d")

    # Prune application_history.csv
    if HISTORY_FILE.exists():
        today_rows = []
        old_rows = []
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if row:
                    if row[0].startswith(today_prefix):
                        today_rows.append(row)
                    else:
                        old_rows.append(row)
        
        if old_rows:
            with open(archive_dir / "history_archive.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(old_rows)
                
            with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Job Title", "Company", "Location", "Job URL", "Status"])
                writer.writerows(today_rows)
            print(f"[DAILY CLEANUP] Archived {len(old_rows)} previous day records. Retained {len(today_rows)} entries for today.")

    # Prune skipped_jobs.csv
    if SKIPPED_FILE.exists():
        today_skips = []
        old_skips = []
        with open(SKIPPED_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if row:
                    if row[0].startswith(today_prefix):
                        today_skips.append(row)
                    else:
                        old_skips.append(row)
                        
        if old_skips:
            with open(archive_dir / "skipped_archive.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(old_skips)
                
            with open(SKIPPED_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Job Title", "Company", "Job URL", "Reason"])
                writer.writerows(today_skips)

def init_logs():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Job Title", "Company", "Location", "Job URL", "Status"])
            
    if not SKIPPED_FILE.exists():
        with open(SKIPPED_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Job Title", "Company", "Job URL", "Reason"])

def log_application(title, company, location, url, status):
    init_logs()
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), title, company, location, url, status])

def log_skipped(title, company, url, reason):
    init_logs()
    with open(SKIPPED_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), title, company, url, reason])

def load_applied_urls():
    init_logs()
    applied_urls = set()
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 5 and row[5] in ["APPLIED", "ALREADY_APPLIED", "DRY_RUN_APPLIED"]:
                    applied_urls.add(row[4])
    return applied_urls

def boost_profile(page, config, dry_run=False):
    print("\n[PROFILE BOOST] Navigating to Naukri Profile...")
    target_headline = config.get("user_profile", {}).get(
        "headline", "DevOps Engineer & Backend Developer (Python / FastAPI / PostgreSQL)"
    )
    
    try:
        page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        headline_card = page.query_selector("div.resumeHeadline, div.card:has-text('Resume headline'), div.widgetTitle:has-text('Resume headline')")
        if headline_card:
            headline_card.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)

        headline_edit = None
        if headline_card:
            edit_cand = headline_card.query_selector("span.edit, em.icon-edit, span.icon")
            if edit_cand:
                headline_edit = edit_cand

        if not headline_edit:
            for el in page.query_selector_all("div.resumeHeadline span.edit, span.edit"):
                if el.is_visible():
                    headline_edit = el
                    break

        if headline_edit:
            try:
                headline_edit.scroll_into_view_if_needed()
                headline_edit.click(timeout=3000)
            except Exception:
                headline_edit.click(force=True, timeout=3000)
            
            # Wait for profile drawer / textarea to load
            try:
                page.wait_for_selector("textarea", timeout=4000)
            except Exception:
                pass
                
            textarea = page.query_selector("textarea#resumeHeadlineTxt, textarea.resumeHeadline, textarea")
            if textarea:
                current_text = textarea.input_value().strip()
                
                if "Platform" in current_text or current_text != target_headline:
                    new_text = target_headline
                else:
                    if current_text.endswith("."):
                        new_text = current_text[:-1]
                    else:
                        new_text = current_text + "."

                if not dry_run:
                    textarea.fill(new_text)
                    page.wait_for_timeout(1000)
                    
                    save_btn = page.query_selector("button:has-text('Save'), button.btn-dark-ot, button[type='submit'], div.action button")
                    if save_btn:
                        save_btn.click(timeout=3000)
                        page.wait_for_timeout(2000)
                        print(f"[PROFILE BOOST] Successfully updated profile headline to:\n '{new_text}'")
                    else:
                        print("[PROFILE BOOST] Could not locate save button for headline.")
                else:
                    print(f"[DRY-RUN] Would update headline from '{current_text}' to '{new_text}'")
            else:
                print("[PROFILE BOOST] Headline text area not found.")
        else:
            print("[PROFILE BOOST] Visible edit headline element not found on profile page.")
    except Exception as e:
        print(f"[PROFILE BOOST ERROR] Profile boost step bypassed safely: {e}")





def handle_questionnaire(job_page, config, dry_run=False):
    profile = config.get("user_profile", {})
    exp = str(profile.get("total_experience_years", 2))
    notice = str(profile.get("notice_period_days", 30))
    current_ctc = str(profile.get("current_ctc_lpa", "6"))
    expected_ctc = str(profile.get("expected_ctc_lpa", "10"))
    loc = profile.get("current_location", "Bengaluru")
    
    try:
        # Give modal 2 seconds to stabilize
        job_page.wait_for_timeout(2000)
        
        # Check for inputs
        inputs = job_page.query_selector_all("div.chatbot input, div.questionnaire input, div.modal-container input, div.apply-message input, textarea")
        for inp in inputs:
            try:
                inp_type = (inp.get_attribute("type") or "text").lower()
                placeholder = (inp.get_attribute("placeholder") or "").lower()
                aria_label = (inp.get_attribute("aria-label") or "").lower()
                name_attr = (inp.get_attribute("name") or "").lower()
                combined = f"{placeholder} {aria_label} {name_attr}"

                if inp_type in ["text", "number"]:
                    if any(k in combined for k in ["exp", "year"]):
                        inp.fill(exp)
                    elif any(k in combined for k in ["notice", "day"]):
                        inp.fill(notice)
                    elif any(k in combined for k in ["expected", "exp ctc"]):
                        inp.fill(expected_ctc)
                    elif any(k in combined for k in ["ctc", "salary", "current"]):
                        inp.fill(current_ctc)
                    elif "location" in combined or "city" in combined:
                        inp.fill(loc)
                    else:
                        inp.fill("Yes")
            except Exception:
                pass

        # Select 'Yes' radio buttons or checkboxes if present
        yes_btns = job_page.query_selector_all("label:has-text('Yes'), input[value='Yes'], button:has-text('Yes')")
        for yb in yes_btns[:3]: # Click up to first 3 Yes options
            try:
                yb.click()
                job_page.wait_for_timeout(300)
            except Exception:
                pass

        # Click submit / save / apply in questionnaire modal
        if not dry_run:
            sub_btn = job_page.query_selector("button:has-text('Submit'), button:has-text('Save'), button:has-text('Apply'), div.bot-submit button, button.submit-btn")
            if sub_btn:
                sub_btn.click()
                job_page.wait_for_timeout(3000)
                return True
        else:
            print("[DRY-RUN] Filled questionnaire answers and would click Submit.")
            return True
            
    except Exception as e:
        print(f"[QUESTIONNAIRE LOG] Exception while answering questions: {e}")
        
    return False

def get_naukri_urls(kw, loc, exp, page_num):
    kw_slug = kw.lower().replace(" ", "-").replace("/", "-")
    loc_slug = loc.lower().replace(" ", "-")
    
    urls = []
    if page_num == 1:
        urls.append(f"https://www.naukri.com/{kw_slug}-jobs-in-{loc_slug}?experience={exp}")
    else:
        urls.append(f"https://www.naukri.com/{kw_slug}-jobs-in-{loc_slug}-{page_num}?experience={exp}")
        
    import urllib.parse
    urls.append(f"https://www.naukri.com/jobs-in-{loc_slug}?k={urllib.parse.quote(kw)}&experience={exp}&pageNo={page_num}")
    return urls

def apply_to_jobs(page, config, dry_run=False):
    applied_urls = load_applied_urls()
    daily_limit = config.get("daily_apply_limit", 100)
    keywords = config.get("keywords", ["Backend Developer", "DevOps Engineer", "FastAPI Developer", "Python Developer", "MLOps Engineer"])
    negative_keywords = config.get("negative_keywords", ["Java", "Spring", "C++", ".NET", "ASP.NET", "C#", "PHP", "Angular", "Ruby", "Android", "iOS"])
    locations = config.get("locations", ["Bangalore"])
    exp = config.get("experience_years", 2)
    
    # Calculate fair quota per category to guarantee a balanced mix of roles across 100 applications
    per_keyword_cap = max(15, daily_limit // len(keywords)) + 3

    total_applied = 0
    print(f"\n[JOB SEARCH] Starting high-yield multi-role search. Target Daily Limit: {daily_limit}")
    print(f"[BALANCED DISTRIBUTION] Max per keyword category: {per_keyword_cap} jobs")
    print(f"[EXCLUSION FILTER] Excluding non-target tech stacks: {', '.join(negative_keywords)}")

    for kw in keywords:
        if total_applied >= daily_limit:
            break
            
        kw_applied = 0

        for loc in locations:
            if total_applied >= daily_limit or kw_applied >= per_keyword_cap:
                break

            for page_num in range(1, 6):
                if total_applied >= daily_limit or kw_applied >= per_keyword_cap:
                    break
                    
                target_urls = get_naukri_urls(kw, loc, exp, page_num)
                job_cards = []
                for search_url in target_urls:
                    print(f"\n[SEARCH: '{kw}' | Page {page_num}] Querying in '{loc}' -> {search_url}")

                    try:
                        page.goto(search_url, wait_until="domcontentloaded")
                        page.wait_for_timeout(3500)
                        
                        try:
                            page.wait_for_selector("div.cust-job-tuple, article.jobTuple, div.srp-jobtuple-wrapper, a.title", timeout=6000)
                        except Exception:
                            pass

                        # Extract job tuples (title, company, link)
                        job_cards = page.query_selector_all("div.cust-job-tuple, article.jobTuple, div.srp-jobtuple-wrapper, div.jobTupleWrapper, div.tuple")
                        if not job_cards:
                            # Fallback query for titles if card wrappers differ
                            title_links = page.query_selector_all("a.title")
                            if title_links:
                                job_cards = title_links
                                print(f"[SEARCH] Found {len(title_links)} title links on page {page_num} for '{kw}'.")
                                break
                        else:
                            print(f"[SEARCH] Found {len(job_cards)} job cards on page {page_num} for '{kw}'.")
                            break
                    except Exception as e:
                        print(f"[SEARCH WARNING] Page fetch warning: {e}")

                if not job_cards:
                    print(f"[SEARCH] No more jobs found on page {page_num} for '{kw}'.")
                    break

                for card in job_cards:
                    if total_applied >= daily_limit or kw_applied >= per_keyword_cap:
                        print(f"[CATEGORY CAP] Quota for '{kw}' ({kw_applied}/{per_keyword_cap}) reached.")
                        break

                    try:
                        title_el = card.query_selector("a.title")
                        company_el = card.query_selector("a.comp-name, a.subTitle")
                        loc_el = card.query_selector("span.locWrd, span.location")

                        if not title_el:
                            continue

                        title = title_el.inner_text().strip()
                        company = company_el.inner_text().strip() if company_el else "Unknown"
                        location_text = loc_el.inner_text().strip() if loc_el else loc
                        job_url = title_el.get_attribute("href")

                        if not job_url or job_url in applied_urls:
                            continue

                        # Mark URL as seen
                        applied_urls.add(job_url)

                        # Check for negative tech keywords (Java, C++, .NET, etc.)
                        neg_matches = [nk for nk in negative_keywords if f" {nk.lower()} " in f" {title.lower()} " or title.lower().startswith(nk.lower() + " ")]
                        if neg_matches:
                            print(f"[EXCLUDED TECH] Skipped: {title} @ {company} (Matches excluded stack: {', '.join(neg_matches)})")
                            log_skipped(title, company, job_url, f"Excluded tech stack: {', '.join(neg_matches)}")
                            continue

                        # Check if card has immediate apply or opens new tab
                        print(f"\n[EVALUATING] {title} at {company}")

                        # Open job in new page/tab to safely process
                        with page.context.expect_page(timeout=10000) as new_page_info:
                            title_el.click()
                        
                        job_page = new_page_info.value
                        job_page.wait_for_load_state("domcontentloaded")
                        job_page.wait_for_timeout(2000)

                        # Check apply buttons
                        apply_btn = job_page.query_selector("button:has-text('Apply'), button#apply-button, button.apply-button")
                        easy_apply = job_page.query_selector("button:has-text('Apply on company site'), button:has-text('Walk-in')")

                        if easy_apply:
                            print(f"[SKIPPED] External company site application: {title} (Logged for 10 LPA Action Dashboard)")
                            log_skipped(title, company, job_url, "External company site")
                            applied_urls.add(job_url)
                            job_page.close()
                            continue

                        if apply_btn:
                            btn_text = apply_btn.inner_text().strip().lower()
                            if "already applied" in btn_text or "applied" == btn_text:
                                print(f"[ALREADY APPLIED] Naukri indicates already applied for: {title}")
                                log_application(title, company, location_text, job_url, "ALREADY_APPLIED")
                                applied_urls.add(job_url)
                                job_page.close()
                                continue

                            if not dry_run:
                                apply_btn.click()
                                job_page.wait_for_timeout(3000)
                                
                                # Check if questionnaire or modal popped up
                                modal_ques = job_page.query_selector("div.chatbot, div.apply-message, div.questionnaire, div.modal-container, div.chatbot-container")
                                if modal_ques:
                                    print(f"[QUESTIONNAIRE] Modal popped up for {title}. Auto-filling answers...")
                                    ans_success = handle_questionnaire(job_page, config, dry_run=False)
                                    if ans_success:
                                        total_applied += 1
                                        kw_applied += 1
                                        print(f"--> [SUCCESS {total_applied}/{daily_limit}] Answered questionnaire & applied to: {title} @ {company}")
                                        log_application(title, company, location_text, job_url, "APPLIED_WITH_QUESTIONNAIRE")
                                    else:
                                        log_skipped(title, company, job_url, "Complex questionnaire")
                                else:
                                    total_applied += 1
                                    kw_applied += 1
                                    print(f"--> [SUCCESS {total_applied}/{daily_limit}] Applied to: {title} @ {company}")
                                    log_application(title, company, location_text, job_url, "APPLIED")
                            else:
                                total_applied += 1
                                kw_applied += 1
                                print(f"--> [DRY-RUN {total_applied}/{daily_limit}] Would click Apply for: {title} @ {company}")
                                log_application(title, company, location_text, job_url, "DRY_RUN_APPLIED")

                            applied_urls.add(job_url)

                        else:
                            print(f"[SKIP] No direct Apply button found for: {title}")
                            log_skipped(title, company, job_url, "No Apply button")
                            applied_urls.add(job_url)

                        job_page.close()
                        
                        # Humanized delay between applications
                        delay = random.uniform(1.8, 3.5)
                        time.sleep(delay)

                    except PlaywrightTimeoutError:
                        print(f"[TIMEOUT] Page load timed out for job: {title if 'title' in locals() else 'Unknown'}")
                    except Exception as ex:
                        print(f"[ERROR] Could not process job card: {ex}")

    print(f"\n==================================================")
    print(f"   BOT SUMMARY: Completed run. Applied to {total_applied} jobs.")
    print(f"==================================================")

def load_clean_storage_state():
    if not AUTH_FILE.exists():
        return None
    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        state_data = json.load(f)
    clean_cookies = [
        c for c in state_data.get("cookies", [])
        if c.get("name") not in ["ak_bmsc", "bm_sv", "HOWTORT"]
    ]
    state_data["cookies"] = clean_cookies
    return state_data

def main():
    parser = argparse.ArgumentParser(description="Automated Daily Naukri Profile Booster & Job Applicator")
    parser.add_argument("--dry-run", action="store_true", help="Run search & checks without applying")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()

    config = load_config()
    is_dry_run = args.dry_run or config.get("dry_run", False)
    is_headless = args.headless or config.get("headless", False)

    # Perform daily log cleanup (retains only today's records for clean reporting)
    purge_previous_days_logs()

    storage_state_arg = load_clean_storage_state()
    if not storage_state_arg:
        print(f"[ERROR] Session authentication file not found at: {AUTH_FILE}")
        print("[ACTION REQUIRED] Please run 'python login.py' first to complete interactive login!")
        sys.exit(1)

    print("Starting Naukri Automation Bot...")
    print(f"Mode: {'[DRY RUN]' if is_dry_run else '[LIVE APPLY]'}")
    print(f"Headless: {is_headless}")

    with sync_playwright() as p:
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080"
        ]
        
        try:
            browser = p.chromium.launch(
                headless=is_headless,
                channel="chrome",
                slow_mo=config.get("slow_mo_ms", 200),
                args=launch_args
            )
        except Exception:
            browser = p.chromium.launch(
                headless=is_headless,
                slow_mo=config.get("slow_mo_ms", 200),
                args=launch_args
            )
        
        # Load saved persistent context with stealth parameters
        context = browser.new_context(
            storage_state=storage_state_arg,
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="Asia/Kolkata",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            }
        )
        page = context.new_page()

        # Mask automation footprint
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        """)

        # 1. Profile Booster
        if config.get("enable_profile_boost", True):
            boost_profile(page, config, dry_run=is_dry_run)

        # 2. Job Search & Auto Apply
        apply_to_jobs(page, config, dry_run=is_dry_run)

        browser.close()

    # Generate daily intelligent action report & HTML dashboard
    try:
        import reporter
        reporter.generate_report()
    except Exception as rep_err:
        print(f"[REPORT ERROR] Could not generate report: {rep_err}")

if __name__ == "__main__":
    main()

