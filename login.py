import os
import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

AUTH_DIR = Path(__file__).parent / "auth"
AUTH_FILE = AUTH_DIR / "storage_state.json"

def is_logged_in(page, context):
    try:
        url = page.url
        if "mnjuser" in url or "my-naukri" in url:
            return True
        
        # Check cookies
        cookies = context.cookies()
        for c in cookies:
            name = c.get("name", "")
            if name in ["nlsid", "Naukri_User", "nUser", "NKUSER"]:
                return True

        # Check DOM elements
        avatar = page.query_selector("a[href*='mnjuser/profile'], div.nNav__user-profile-img, span.user-name, div.crossIcon")
        if avatar:
            return True
    except Exception:
        pass
    return False

def run_login():
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    
    config_path = Path(__file__).parent / "config.json"
    login_url = "https://www.naukri.com/nlogin/login"

    print("==================================================================")
    print("      NAUKRI AUTO-APPLY: ONE-TIME INTERACTIVE LOGIN SESSION       ")
    print("==================================================================")
    print("1. Opening Google Chrome browser...")
    print("2. Please click 'Sign in with Google' and complete sign-in.")
    print("3. The script will AUTO-SAVE your login as soon as you sign in!")
    print("==================================================================")

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(
                channel="chrome",
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
            )
            print("[INFO] Launched Google Chrome.")
        except Exception:
            browser = p.chromium.launch(
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
            )
            print("[INFO] Launched Chromium browser.")

        context = browser.new_context(
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(login_url, wait_until="domcontentloaded")

        print("\n[WAITING] Waiting for you to complete Google / Naukri login in Chrome...")

        saved = False
        start_time = time.time()

        # Monitor loop (5 minutes max timeout)
        while time.time() - start_time < 300:
            if page.is_closed():
                print("[INFO] Browser window closed.")
                break

            if is_logged_in(page, context):
                page.wait_for_timeout(2000) # wait for cookies to settle
                context.storage_state(path=str(AUTH_FILE))
                print(f"\n[SUCCESS] Login detected! Authentication session saved to:")
                print(f"--> {AUTH_FILE}")
                saved = True
                break

            time.sleep(1.5)

        if not saved:
            # Fallback: try saving state before exit
            try:
                context.storage_state(path=str(AUTH_FILE))
                if AUTH_FILE.exists() and AUTH_FILE.stat().st_size > 50:
                    print(f"\n[SUCCESS] Saved session state to {AUTH_FILE}")
                    saved = True
            except Exception as e:
                print(f"[ERROR] Could not save state: {e}")

        if saved:
            print("\n[COMPLETE] You are all set! Daily background runs will now work automatically.")
        else:
            print("\n[WARNING] Session file was not saved. Please try running login.py again and completing sign in.")

        try:
            browser.close()
        except Exception:
            pass

if __name__ == "__main__":
    run_login()
