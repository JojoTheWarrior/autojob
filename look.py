from fastapi import FastAPI
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common import *
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup, Tag, NavigableString
from collections import deque
import sys
import threading
import time
import re
import json
import os
from datetime import datetime, timezone

from look_actions import want_actions, execute_actions
from extraction import extract_info, safe_click

app = FastAPI(title="autojob API")

class ApplyRequest(BaseModel):
    url: str

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

driver = ""
actor_bullshit = []
critic_bullshit = []

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

def pad_numbers(x):
    x = str(x)
    while len(x) < 5:
        x = "0" + x
    return x

def prune_tree_by_keyword(soup, keyword):
    keyword = keyword.lower().strip()

    nodes_to_delete = []

    def prune(node):
        # Text node
        if isinstance(node, NavigableString):
            return keyword in str(node).lower()

        if not isinstance(node, Tag):
            return False

        keep = False

        for child in list(node.children):
            if prune(child):
                keep = True
            else:
                if isinstance(child, Tag):
                    nodes_to_delete.append(child)

        # Check this node's own visible text
        own_text = node.get_text(strip=True).lower()
        if keyword in own_text:
            keep = True

        return keep

    prune(soup)

    # Delete only after traversal finishes
    for node in nodes_to_delete:
        node.decompose()

    return soup
        
def strip_code_fences(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        # Remove first line (```python or ```)
        lines = lines[1:]

        # Remove last line if it's closing ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        return "\n".join(lines).strip()

    return text

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

@app.get("/get_actor")
def get_actor():
    global actor_bullshit
    return actor_bullshit

@app.get("/get_critic")
def get_critic():
    global critic_bullshit
    return critic_bullshit

@app.post("/apply")
def apply(req: ApplyRequest):
    url = req.url
    t = threading.Thread(target=startApp, args=(url,))
    t.daemon = True
    t.start()

    # instantly returns something
    return {
        "status": "ok",
        "message": "job started",
        "url": req.url
    }

def startApp(url):
    global driver
    global actor_bullshit
    global critic_bullshit
    driver = get_driver(options)

    run_number = 0

    print("HELLO")

    with open("./screenshots/run_number.txt", "r") as f:
        run_number = int(f.read())

    with open("./screenshots/run_number.txt", "w") as f:
            f.write(str(run_number + 1))

    os.makedirs(f"./screenshots/run_{pad_numbers(run_number)}")

    try:
        print(f"Opening {url}")
        driver.get(url)

        WebDriverWait(driver, timeout=15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        frame_number = 0
        past_commands = ""
        past_wants = deque()

        while frame_number < 100:
            screenshot_path = f"./screenshots/run_{pad_numbers(run_number)}/current_{pad_numbers(frame_number)}.png"
            driver.save_screenshot(screenshot_path)
            gb = want_actions(screenshot_path, past_wants)

            print(gb)
            html = driver.page_source

            if gb == "Done":
                break
            elif gb == "Scroll":
                driver.execute_script("window.scrollBy(0, 1000);")
            else:
                print("Here at splitter")
                gb = gb.split("\n")
                gb[:] = [item for item in gb if item != '']
                print(gb)

                past_commands = gb[0]
                keywords = gb[1]

                actor_bullshit.append((datetime.now(timezone.utc).isoformat(), past_commands))

                past_wants.append(past_commands)
                if len(past_wants) > 10:
                    past_wants.popleft()

                soup = BeautifulSoup(html, "html.parser")
                pruned_soup = prune_tree_by_keyword(soup, keywords)

                if keywords.lower().strip() == "cookies":
                    pruned_soup = soup
                
                with open(f"./screenshots/run_{pad_numbers(run_number)}/current_{pad_numbers(frame_number)}_soup.txt", "w", encoding="utf-8") as f:
                    f.write(str(pruned_soup))

                cmds = strip_code_fences(execute_actions(str(pruned_soup), past_commands))

                print(cmds)

                for cmd in cmds.split("\n"):
                    critic_bullshit.append(cmd)

                try:
                    exec(cmds)
                except Exception as e:
                    print("smth went wrong in execution")

            frame_number += 1
        
        print("Done. User free to roam.")

        time.sleep(60)
        
    except Exception as e:
        print(e)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "look:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )