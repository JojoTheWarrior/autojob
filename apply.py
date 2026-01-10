from fastapi import FastAPI
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
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

        # blindly sleeps for 5 seconds, just to wait for the page to load
        time.sleep(5)

        html = driver.page_source
        
        try:
            with open("rbc_html.txt", "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print("error writing into html.txt")
        
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
                "css_path": css_path(el),
                "label": find_label_text(el) if el.name in ["input", "textarea", "select"] else None
            }

            # Drop empty noise nodes
            if record["text"] or record["id"] or record["name"]:
                elements.append(record)
                # Select Country - Canada (since this is RBC)
        
        # instructions to run 
        country_select = Select(driver.find_element(By.ID, "country"))
        country_select.select_by_visible_text("Canada")
        time.sleep(0.5)

        # Select Prefix
        prefix_select = Select(driver.find_element(By.ID, "cntryFields.nameTitle"))
        prefix_select.select_by_visible_text("Mr.")
        time.sleep(0.5)

        # First Name
        driver.find_element(By.ID, "cntryFields.firstName").send_keys("John")
        time.sleep(0.5)

        # Middle Name (optional)
        driver.find_element(By.ID, "cntryFields.middleName").send_keys("")
        time.sleep(0.5)

        # Last Name
        driver.find_element(By.ID, "cntryFields.lastName").send_keys("Doe")
        time.sleep(0.5)

        # Preferred Name dropdown
        preferred_name_select = Select(driver.find_element(By.ID, "cntryFields.preferredName"))
        preferred_name_select.select_by_visible_text("No")
        time.sleep(0.5)

        # Address Line 1
        driver.find_element(By.ID, "cntryFields.addressLine1").send_keys("123 Main Street")
        time.sleep(0.5)

        # Address Line 2 (optional)
        driver.find_element(By.ID, "cntryFields.addressLine2").send_keys("")
        time.sleep(0.5)

        # City
        driver.find_element(By.ID, "cntryFields.city").send_keys("Toronto")
        time.sleep(0.5)

        # Province or Territory
        region_select = Select(driver.find_element(By.ID, "cntryFields.region"))
        region_select.select_by_visible_text("Ontario")
        time.sleep(0.5)

        # Postal Code
        driver.find_element(By.ID, "cntryFields.postalCode").send_keys("M5V 1A1")
        time.sleep(0.5)

        # Email address
        driver.find_element(By.ID, "email").send_keys("john.doe@email.com")
        time.sleep(0.5)

        # Phone Device Type
        device_type_select = Select(driver.find_element(By.ID, "deviceType"))
        time.sleep(0.5)
        device_type_select.select_by_visible_text("Mobile")
        time.sleep(0.5)
        device_type_select.select_by_visible_text("Mobile")
        time.sleep(0.5)

        # Country Phone Code
        phone_code_select = Select(driver.find_element(By.ID, "phoneWidget.countryPhoneCode"))
        phone_code_select.select_by_visible_text("Canada (+1)")
        time.sleep(0.5)

        # Phone number
        driver.find_element(By.ID, "phoneWidget.phoneNumber").send_keys("4165551234")
        time.sleep(0.5)

        # How did you hear about us?
        source_select = Select(driver.find_element(By.ID, "source"))
        source_select.select_by_visible_text("Corporate Website")
        time.sleep(0.5)

        # Have you worked for RBC?
        worked_rbc_select = Select(driver.find_element(By.ID, "haveYouWorkedForRbc"))
        worked_rbc_select.select_by_visible_text("No")
        time.sleep(0.5)

        # Click Next button
        driver.find_element(By.ID, "next").click()

        with open("rbc_extraction.json", "w", encoding="utf-8") as f:
            json.dump(elements, f, indent=2)

        # let user 
        time.sleep(60)


    finally:
        driver.quit()

if __name__ == "__main__":
    main()