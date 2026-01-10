from fastapi import FastAPI
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import sys
import threading
import time
import re
import json

app = FastAPI()


def main():
    if len(sys.argv) < 2:
        print("Usage: python dump_html.py <url>")
        return

    url = sys.argv[1]

    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/114.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)

    try:
        print(f"Opening {url}")
        driver.get(url)

        # just opens the page
        WebDriverWait(driver, timeout=15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        html = driver.page_source
        
        with open("voltair_html.txt", "w") as f:
            f.write(html)
        
        USEFUL_TAGS = [
            "h1", "h2", "h3", "h4",
            "p", "li", "span", "strong", "em",
            "a", "button",
            "input", "textarea", "select", "option", "label"
        ]

        soup = BeautifulSoup(html, "html.parser")

        # css path for an element
        def css_path(el):
            path = []
            while el and el.name != "[document]":
                name = el.name

                if el.get("id"):
                    name += f"#{el.get('id')}"
                    path.insert(0, name)
                    break

                siblings = el.find_previous_siblings(el.name)
                if siblings:
                    name += f":nth-of-type({len(siblings) + 1})"

                path.insert(0, name)
                el = el.parent

            return " > ".join(path)

        # takes text and removes leading / trailing whitespace
        def clean_text(text):
            if not text:
                return ""
            text = re.sub(r"\s+", " ", text)
            return text.strip()

        def find_label_text(el):
            # Case 1: <label for="inputId">
            el_id = el.get("id")
            if el_id:
                label = soup.find("label", attrs={"for": el_id})
                if label:
                    return clean_text(label.get_text())

            # Case 2: input wrapped by label
            parent_label = el.find_parent("label")
            if parent_label:
                return clean_text(parent_label.get_text())

            return None

        # starts extracting the useful elements
        elements = []  

        for el in soup.find_all(list(USEFUL_TAGS)):
            text = clean_text(el.get_text())

            attrs = el.attrs or {}

            record = {
                "tag": el.name,
                "text": text,
                "id": attrs.get("id"),
                "class": " ".join(attrs.get("class", [])) if isinstance(attrs.get("class"), list) else attrs.get("class"),
                "name": attrs.get("name"),
                "type": attrs.get("type"),
                "placeholder": attrs.get("placeholder"),
                "href": attrs.get("href"),
                "aria_label": attrs.get("aria-label"),
                "aria_role": attrs.get("role"),
                "disabled": "disabled" in attrs,
                "required": "required" in attrs,
                "css_path": css_path(el),
                "label": find_label_text(el) if el.name in ["input", "textarea", "select"] else None
            }

            # Drop empty noise nodes
            if record["text"] or record["id"] or record["name"] or record["aria_label"]:
                elements.append(record)

        with open("voltair_extraction.json", "w") as f:
            json.dump(elements, f, indent=2)

        username_input = driver.find_element(By.ID, "ycid-input")
        username_input.clear()
        username_input.send_keys("your_username_or_email")

        # Fill password input (id=password-input)
        password_input = driver.find_element(By.ID, "password-input")
        password_input.clear()
        password_input.send_keys("your_secure_password")

        # Click the login button (css selector from json)
        login_button = driver.find_element(By.CSS_SELECTOR, "form#sign-in-card > div:nth-of-type(4) > button")
        login_button.click()

        # let user 
        time.sleep(60)


    finally:
        driver.quit()

if __name__ == "__main__":
    main()