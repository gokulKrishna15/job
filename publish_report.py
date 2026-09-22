import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
REPORT_FILE = BASE_DIR / "reports" / "latest_report.html"
DOCS_DIR = BASE_DIR / "docs"

def prepare_github_pages():
    """
    Copies latest_report.html to docs/index.html.
    If Gokul pushes this project to GitHub and turns on GitHub Pages (Source: docs folder),
    his live job dashboard will be hosted online 100% FREE at:
    https://<username>.github.io/<repo-name>/
    """
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    if REPORT_FILE.exists():
        shutil.copy(str(REPORT_FILE), str(DOCS_DIR / "index.html"))
        print("==================================================================")
        print("   FREE ONLINE HOSTING UTILITY (GITHUB PAGES / NETLIFY)          ")
        print("==================================================================")

        print(f"--> Copied latest report to: {DOCS_DIR / 'index.html'}")
        print("\nTo access your report from your phone anywhere in the world:")
        print("1. Push this folder to a GitHub repository.")
        print("2. Go to Repo Settings -> Pages -> Select 'main' branch and '/docs' folder.")
        print("3. Your report will be live online 24/7 for FREE!")
        print("==================================================================")

if __name__ == "__main__":
    prepare_github_pages()
