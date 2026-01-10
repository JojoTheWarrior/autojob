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
import os

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

    driver = get_driver(options)

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
        #-------------------
        
        # Click the "Upload resume" button first
        driver.find_element(By.CSS_SELECTOR, "button.upload-resume-btn").click()
        time.sleep(0.5)

        # Wait for file input to appear and upload resume
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        


        # Select Country - Canada
        Select(driver.find_element(By.ID, "country")).select_by_visible_text("Canada")
        time.sleep(0.5)

        # Select Prefix - Mr.
        Select(driver.find_element(By.ID, "cntryFields.nameTitle")).select_by_visible_text("Mr.")
        time.sleep(0.5)

        # Fill First Name
        driver.find_element(By.ID, "cntryFields.firstName").send_keys("John")
        time.sleep(0.5)

        # Fill Middle Name (optional)
        driver.find_element(By.ID, "cntryFields.middleName").send_keys("Michael")
        time.sleep(0.5)

        # Fill Last Name
        driver.find_element(By.ID, "cntryFields.lastName").send_keys("Smith")
        time.sleep(0.5)

        # Select preferred name - No
        Select(driver.find_element(By.ID, "cntryFields.preferredName")).select_by_visible_text("No")
        time.sleep(0.5)

        # Fill Address Line 1
        driver.find_element(By.ID, "cntryFields.addressLine1").send_keys("123 Main Street")
        time.sleep(0.5)

        # Fill Address Line 2 (optional)
        driver.find_element(By.ID, "cntryFields.addressLine2").send_keys("Apt 456")
        time.sleep(0.5)

        # Fill City
        driver.find_element(By.ID, "cntryFields.city").send_keys("Toronto")
        time.sleep(0.5)

        # Select Province - Ontario
        Select(driver.find_element(By.ID, "cntryFields.region")).select_by_visible_text("Ontario")
        time.sleep(0.5)

        # Fill Postal Code
        driver.find_element(By.ID, "cntryFields.postalCode").send_keys("M5V 1A1")
        time.sleep(0.5)

        # Fill Email
        driver.find_element(By.ID, "email").send_keys("john.smith@email.com")
        time.sleep(0.5)

        # Select Phone Device Type - Mobile
        Select(driver.find_element(By.ID, "deviceType")).select_by_visible_text("Mobile")
        time.sleep(0.5)

        # Select Country Phone Code - Canada (+1)
        Select(driver.find_element(By.ID, "phoneWidget.countryPhoneCode")).select_by_visible_text("Canada (+1)")
        time.sleep(0.5)

        # Fill Phone Number
        driver.find_element(By.ID, "phoneWidget.phoneNumber").send_keys("4165551234")
        time.sleep(0.5)

        # Select How did you hear about us - Job Board
        Select(driver.find_element(By.ID, "source")).select_by_visible_text("Job Board")
        time.sleep(0.5)

        # Select Source - Indeed
        Select(driver.find_element(By.ID, "applicantSource")).select_by_visible_text("Indeed")
        time.sleep(0.5)

        # Select Have you worked for RBC - No
        Select(driver.find_element(By.ID, "haveYouWorkedForRbc")).select_by_visible_text("No")
        time.sleep(0.5)

        # Click Next button
        driver.find_element(By.ID, "next").click()
        time.sleep(0.5)

        #--------------

        with open("rbc_extraction.json", "w", encoding="utf-8") as f:
            json.dump(elements, f, indent=2)

        # let user 
        time.sleep(60)


    finally:
        driver.quit()

def upload_file(input_element, type, driver):
    if type == "resume":
        abs_path = os.path.abspath("resumes/resume.pdf")
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