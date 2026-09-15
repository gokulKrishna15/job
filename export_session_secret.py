import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
AUTH_FILE = BASE_DIR / "auth" / "storage_state.json"

def export_secret():
    if not AUTH_FILE.exists():
        print("[ERROR] auth/storage_state.json does not exist. Run 'python login.py' first.")
        return

    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        secret_content = f.read().strip()

    print("==================================================================")
    print("   🔑 GITHUB SECRET EXTRACTOR (FOR 100% FREE LAPTOP-FREE BOT)     ")
    print("==================================================================")
    print("To enable daily cloud runs on GitHub (without turning on your laptop):\n")
    print("1. Go to your GitHub Repository -> Settings -> Secrets and variables -> Actions")
    print("2. Click 'New repository secret'")
    print("3. Secret Name: NAUKRI_STORAGE_STATE")
    print("4. Secret Value: (Copy and paste the JSON block below)\n")
    print("-------------------- COPY FROM HERE --------------------")
    print(secret_content)
    print("--------------------- COPY TO HERE ---------------------\n")
    print("[SUCCESS] After pasting into GitHub Secrets, your bot runs automatically 24/7 in the cloud for FREE!")

if __name__ == "__main__":
    export_secret()
