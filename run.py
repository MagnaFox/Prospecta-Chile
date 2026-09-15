"""
Launcher for ProspectaChile B2B
"""
import webbrowser
import threading
import time
from server import run_server

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://localhost:8080")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    run_server()
