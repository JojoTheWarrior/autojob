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

def extract_info(html):
    soup = BeautifulSoup(html, "html.parser")

    # ---------------------------
    # Configuration
    # ---------------------------

    USEFUL_TAGS = {
        "h1", "h2", "h3", "h4",
        "p", "li", "span", "strong", "em",
        "a", "button",
        "input", "textarea", "select", "option", "label",
        "div"   # important for modern UI widgets
    }

    INTERACTIVE_ATTRS = [
        "onclick",
        "tabindex",
        "contenteditable",
        "aria-label",
        "aria-expanded",
        "aria-controls",
        "aria-haspopup"
    ]

    INTERACTIVE_ROLES = {
        "button", "combobox", "listbox", "option",
        "menu", "menuitem",
        "textbox", "dialog",
        "checkbox", "radio"
    }

    # ---------------------------
    # Utilities
    # ---------------------------

    def clean_text(text):
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

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

    # ---------------------------
    # Heuristics
    # ---------------------------

    def is_useful(el):
        # Native useful tags
        if el.name in USEFUL_TAGS:
            return True

        # Has visible text
        if clean_text(el.get_text()):
            return True

        # Has interactive attributes
        for attr in INTERACTIVE_ATTRS:
            if el.has_attr(attr):
                return True

        # Has ARIA role
        role = el.get("role")
        if role and role.lower() in INTERACTIVE_ROLES:
            return True

        return False

    def infer_semantic_type(el):
        role = (el.get("role") or "").lower()
        tag = el.name.lower()
        text = clean_text(el.get_text()).lower()

        if tag == "select":
            return "native_select"

        if role == "combobox":
            return "custom_select_trigger"

        if role == "listbox":
            return "custom_option_container"

        if role == "option":
            return "custom_option"

        if tag in ["input", "textarea"]:
            return "text_input"

        if tag in ["button", "a"] or role == "button":
            return "button"

        # Heuristic for fake clickable divs
        if tag == "div" and (
            el.has_attr("onclick")
            or el.get("tabindex") is not None
            or "select" in text
            or "choose" in text
        ):
            return "clickable_div"

        return None

    def is_clickable(el):
        role = (el.get("role") or "").lower()
        return (
            el.name in ["button", "a"]
            or el.has_attr("onclick")
            or el.get("tabindex") is not None
            or role in ["button", "option", "combobox", "menuitem"]
        )

    # ---------------------------
    # Option Extraction
    # ---------------------------

    def extract_native_options(el):
        """
        Extracts <select><option> and <input list=...> options.
        """
        options = []

        # <select><option>
        if el.name == "select":
            for opt in el.find_all("option"):
                options.append({
                    "value": opt.get("value"),
                    "text": clean_text(opt.get_text()),
                    "selected": opt.has_attr("selected"),
                    "disabled": opt.has_attr("disabled"),
                })

        # <input list="countries"> + <datalist>
        elif el.name == "input" and el.get("list"):
            datalist_id = el.get("list")
            datalist = soup.find("datalist", {"id": datalist_id})
            if datalist:
                for opt in datalist.find_all("option"):
                    options.append({
                        "value": opt.get("value"),
                        "text": clean_text(opt.get_text()),
                    })

        return options or None

    def extract_custom_options(el):
        """
        Attempts to infer options for ARIA widgets like combobox/listbox.
        """
        role = (el.get("role") or "").lower()
        options = []

        # If this is a listbox, its children are often options
        if role == "listbox":
            for child in el.find_all(attrs={"role": "option"}):
                options.append({
                    "text": clean_text(child.get_text()),
                    "css_path": css_path(child)
                })

        # If this is a combobox, try aria-controls target
        if role == "combobox":
            controls_id = el.get("aria-controls")
            if controls_id:
                container = soup.find(id=controls_id)
                if container:
                    for child in container.find_all(attrs={"role": "option"}):
                        options.append({
                            "text": clean_text(child.get_text()),
                            "css_path": css_path(child)
                        })

        return options or None

    # ---------------------------
    # Extraction
    # ---------------------------

    elements = []

    for el in soup.find_all(is_useful):
        attrs = el.attrs or {}
        text = clean_text(el.get_text())

        native_options = extract_native_options(el)
        custom_options = extract_custom_options(el)

        semantic_type = infer_semantic_type(el)

        record = {
            "tag": el.name,
            "text": text,

            # Identifiers
            "id": attrs.get("id"),
            "class": " ".join(attrs.get("class", [])) if isinstance(attrs.get("class"), list) else attrs.get("class"),
            "name": attrs.get("name"),

            # Input metadata
            "type": attrs.get("type"),
            "placeholder": attrs.get("placeholder"),
            "value": attrs.get("value"),

            # Links
            "href": attrs.get("href"),

            # Accessibility / behavior
            "role": attrs.get("role"),
            "aria_label": attrs.get("aria-label"),
            "aria_expanded": attrs.get("aria-expanded"),
            "aria_controls": attrs.get("aria-controls"),
            "tabindex": attrs.get("tabindex"),
            "contenteditable": el.has_attr("contenteditable"),

            # Semantics
            "label": find_label_text(el) if el.name in ["input", "textarea", "select"] else None,
            "semantic_type": semantic_type,
            "is_clickable": is_clickable(el),

            # Structure
            "css_path": css_path(el),
            "parent_tag": el.parent.name if el.parent else None,
            "parent_role": el.parent.get("role") if el.parent else None,
            "depth": len(list(el.parents)),

            # Options
            "options": native_options or custom_options,
            "multiple": el.has_attr("multiple") if el.name == "select" else False,
        }

        # Smarter noise filter
        if (
            record["text"]
            or record["id"]
            or record["name"]
            or record["role"]
            or record["aria_label"]
            or record["semantic_type"]
        ):
            elements.append(record)

    return elements


# for safely clicking buttons
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

def safe_click(driver, element, timeout=10):
    # Wait until element is actually clickable
    WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(element)
    )

    # Scroll into view (centered)
    driver.execute_script("""
        arguments[0].scrollIntoView({
            behavior: 'instant',
            block: 'center',
            inline: 'center'
        });
    """, element)

    time.sleep(0.2)

    try:
        element.click()
        return

    except Exception:
        pass

    # Fallback 1 — click via JS (ignores overlays)
    try:
        driver.execute_script("arguments[0].click();", element)
        return
    except Exception:
        pass

    # Fallback 2 — ActionChains click
    try:
        ActionChains(driver).move_to_element(element).pause(0.1).click().perform()
        return
    except Exception:
        pass

    raise RuntimeError("safe_click failed for element")
