from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
import asyncio
from datetime import datetime, timezone

from look_actions import want_actions, execute_actions
from extraction import extract_info, safe_click

from fastapi.middleware.cors import CORSMiddleware  # Add this import

app = FastAPI(title="autojob API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Failed to send to websocket: {e}")

    def broadcast_sync(self, message: str):
        """Synchronous broadcast for use in threads - creates a new event loop"""
        for connection in self.active_connections:
            try:
                asyncio.run(connection.send_text(message))
            except RuntimeError:
                # If there's already an event loop running, use it
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(connection.send_text(message))
                except Exception as e:
                    print(f"Broadcast error: {e}")
            except Exception as e:
                print(f"Failed to send to websocket: {e}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # If you don't care about messages from client, you can still
            # keep the loop alive by reading:
            data = await websocket.receive_text()
            # Optional: echo or handle incoming data
            await websocket.send_text(f"You said: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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
actor_word = "Initializing..."

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

@app.get("/similar")
async def get_similar():
    """Returns the current actor_word for the neural graph."""
    global actor_word
    await manager.broadcast(actor_word)
    return {"status": "sent"}

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
    global actor_word
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
            print(f"\n{'='*60}")
            print(f"[DEBUG] === FRAME {frame_number} ===")
            print(f"{'='*60}")
            
            screenshot_path = f"./screenshots/run_{pad_numbers(run_number)}/current_{pad_numbers(frame_number)}.png"
            print(f"[DEBUG] Saving screenshot to: {screenshot_path}")
            driver.save_screenshot(screenshot_path)
            
            print(f"[DEBUG] Calling want_actions (Critic)...")
            print(f"[DEBUG] Past wants: {list(past_wants)}")
            gb = want_actions(screenshot_path, past_wants)

            print(f"[DEBUG] Critic raw response:\n---\n{gb}\n---")
            html = driver.page_source
            print(f"[DEBUG] Page source length: {len(html)} chars")

            if gb == "Done":
                print(f"[DEBUG] Critic returned 'Done' - application complete!")
                break
            elif gb == "Scroll":
                print(f"[DEBUG] Critic returned 'Scroll' - scrolling page...")
                driver.execute_script("window.scrollBy(0, 1000);")
            else:
                print(f"[DEBUG] Critic returned action - parsing...")
                gb = gb.split("\n")
                gb[:] = [item for item in gb if item != '']
                print(f"[DEBUG] Parsed lines ({len(gb)} total): {gb}")
                
                if len(gb) < 2:
                    print(f"[WARN] Expected 2 lines (action + keyword), got {len(gb)}. Raw: {gb}")
                    frame_number += 1
                    continue

                past_commands = gb[0]
                keywords = gb[1]
                
                print(f"[DEBUG] Action requested: '{past_commands}'")
                print(f"[DEBUG] Keyword to search: '{keywords}'")

                actor_bullshit.append((datetime.now(timezone.utc).isoformat(), past_commands))

                past_wants.append(past_commands)
                if len(past_wants) > 10:
                    past_wants.popleft()

                soup = BeautifulSoup(html, "html.parser")
                print(f"[DEBUG] Pruning HTML tree by keyword: '{keywords}'")
                pruned_soup = prune_tree_by_keyword(soup, keywords)

                if keywords.lower().strip() == "cookies":
                    print(f"[DEBUG] Cookie mode - using full soup")
                    pruned_soup = soup
                
                pruned_html = str(pruned_soup)
                print(f"[DEBUG] Pruned HTML length: {len(pruned_html)} chars")
                
                with open(f"./screenshots/run_{pad_numbers(run_number)}/current_{pad_numbers(frame_number)}_soup.txt", "w", encoding="utf-8") as f:
                    f.write(pruned_html)

                print(f"[DEBUG] Calling execute_actions (Actor)...")
                actor_response = strip_code_fences(execute_actions(pruned_html, past_commands))
                print(f"[DEBUG] Actor raw response:\n---\n{actor_response}\n---")
                
                actor_response = actor_response.split("\n")
                if len(actor_response) < 2:
                    print(f"[WARN] Actor response has < 2 lines. Skipping execution.")
                    frame_number += 1
                    continue
                    
                actor_word, cmds = actor_response[0], "\n".join(actor_response[1:])
                print(f"[DEBUG] Actor word: '{actor_word}'")
                print(f"[DEBUG] Generated Selenium commands ({len(cmds)} chars):")
                for i, line in enumerate(cmds.split("\n")):
                    print(f"  [{i}] {line}")

                # Broadcast the actor_word to all connected WebSocket clients
                try:
                    manager.broadcast_sync(json.dumps({"type": "actor_word", "word": actor_word}))
                    print(f"[DEBUG] WebSocket broadcast sent: {actor_word}")
                except Exception as e:
                    print(f"[ERROR] WebSocket broadcast failed: {e}")

                for cmd in cmds.split("\n"):
                    critic_bullshit.append(cmd)

                print(f"[DEBUG] Executing Selenium commands...")
                try:
                    exec(cmds)
                    print(f"[DEBUG] Execution completed successfully")
                except Exception as e:
                    print(f"[ERROR] Execution failed: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()

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