#!/usr/bin/env python3
import os
import subprocess
import time
from playwright.sync_api import sync_playwright

def start_vnc_services():
    """Start VNC services on local machine"""
    print("🚀 Starting VNC services...")

    # Start Xvfb
    subprocess.Popen([
        "Xvfb", ":99", "-screen", "0", "1920x1080x24", "-ac"
    ])
    time.sleep(2)

    # Start x11vnc
    subprocess.Popen([
        "x11vnc", "-display", ":99", "-forever", "-shared",
        "-rfbport", "5901", "-nopw"
    ])
    time.sleep(2)

    print("✅ VNC started on :99 (port 5901)")

def start_browser():
    """Start browser with Playwright on display :99"""
    os.environ["DISPLAY"] = ":99"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.get_page()
        page.goto("https://google.com")
        print("✅ Browser started on display :99")

        # Keep browser open
        input("Press Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    print("🧪 Simple VNC + Browser Test")
    start_vnc_services()
    start_browser()