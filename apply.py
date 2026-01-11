from fastapi import FastAPI
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common import *
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import sys
import threading
import time
import re
import json
import os

from look_actions import get_actions
from extraction import extract_info, safe_click

# initializes selenium driver
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/114.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

app = FastAPI()

def get_driver(options):
    """Attempts to get a driver for Chrome, then Firefox, then Safari."""
    # Try Chrome
    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Chrome not available: {e}")

    # Try Firefox
    try:
        options = webdriver.FirefoxOptions()
        return webdriver.Firefox(options=options)
    except Exception as e:
        print(f"Firefox not available: {e}")

    # Try Safari (macOS only)
    if sys.platform == "darwin":
        try:
            return webdriver.Safari()
        except Exception as e:
            print(f"Safari not available: {e}")

    raise Exception("No supported browser driver found.")

driver = get_driver(options)

def main():
    if len(sys.argv) < 2:
        print("Usage: python dump_html.py <url>")
        return

    url = sys.argv[1]

    try:
        print(f"Opening {url}")
        driver.get(url)

        previous_failure = ""
        previous_try = ""
        previous_attempt_count = 0

        while True:
            # just opens the page
            WebDriverWait(driver, timeout=15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            html = driver.page_source
            
            try:
                with open("rbc_html.txt", "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception as e:
                print("error writing into html.txt")
            
            # extract_info(html) function from extraction.py
            info = extract_info(html)

            with open("rbc_extraction.json", "w", encoding="utf-8") as f:
                json.dump(info, f, indent=2)
            
            gb = get_actions(str(info), previous_failure, previous_try, previous_attempt_count)
            print(gb)

            if gb == "DONE":
                break

            # this is crazy
            try:
                exec(gb)
                previous_attempt_count = 0
            except Exception as e:
                previous_failure = str(e)
                previous_try = gb
                previous_attempt_count += 1
                print(previous_failure)
                pass

        print("Deemed DONE. User free to roam.")

        # let user 
        time.sleep(60)

    finally:
        driver.quit()

def upload_file(input_element, type):
    global driver
    if type == "resume":
        abs_path = os.path.abspath("resumes/resume.pdf")
        print(abs_path)
        input_element.send_keys(abs_path)
    if type == "cv":
        abs_path = os.path.abspath("cvs/cv.pdf")
        input_element.send_keys(abs_path)

    time.sleep(1.0)
    # Handle "Upload Successful" alert if it appears
    try:
        alert = driver.switch_to.alert
        alert.accept()
        time.sleep(0.5) 
    except Exception:
            # It's okay if no alert appears, or if we missed it (though unlikely with sleep)
            
        pass

if __name__ == "__main__":
    main()