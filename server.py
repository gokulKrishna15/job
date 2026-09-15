import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8000
BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"

class ReportHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Default to latest_report.html
        if path == "/" or path == "/index.html":
            return str(REPORTS_DIR / "latest_report.html")
        elif path.startswith("/reports/"):
            return str(BASE_DIR / path.lstrip("/"))
        return super().translate_path(path)

def start_server():
    os.chdir(str(BASE_DIR))
    handler = ReportHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}"
        print("==================================================================")
        print(f"   🚀 NAUKRI JOB DASHBOARD WEB SERVER LIVE AT: {url}")
        print("==================================================================")
        print("--> Accessible on your laptop & any device on your Wi-Fi network!")
        print("--> Press CTRL+C to stop the server.")
        print("------------------------------------------------------------------")
        
        try:
            webbrowser.open(url)
        except Exception:
            pass
            
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    start_server()
