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

    def is_useful(el):
        if el.name in USEFUL_TAGS:
            return True

        # Has visible text
        if clean_text(el.get_text()):
            return True

        # Has interactive attributes
        for attr in INTERACTIVE_ATTRS:
            if el.has_attr(attr):
                return True

        # Has aria role
        if el.get("role"):
            return True

        return False

    USEFUL_TAGS = [
        "h1", "h2", "h3", "h4",
        "p", "li", "span", "strong", "em",
        "a", "button",
        "input", "textarea", "select", "option", "label"
    ]

    # starts extracting the useful elements
    elements = []  

    for el in soup.find_all(list(USEFUL_TAGS)):
        text = clean_text(el.get_text())

        attrs = el.attrs or {}

        options = None

        # <select><option>...</option></select>
        if el.name == "select":
            options = []
            for opt in el.find_all("option"):
                options.append({
                    "value": opt.get("value"),
                    "text": clean_text(opt.get_text()),
                    "selected": opt.has_attr("selected"),
                    "disabled": opt.has_attr("disabled"),
                })

        # <input list="countries"> + <datalist id="countries">
        elif el.name == "input" and el.get("list"):
            datalist_id = el.get("list")
            datalist = soup.find("datalist", {"id": datalist_id})
            if datalist:
                options = []
                for opt in datalist.find_all("option"):
                    options.append({
                        "value": opt.get("value"),
                        "text": clean_text(opt.get_text()),
                    })

        record = {
            "tag": el.name,
            "text": text,
            "id": attrs.get("id"),
            "class": " ".join(attrs.get("class", [])) if isinstance(attrs.get("class"), list) else attrs.get("class"),
            "name": attrs.get("name"),
            "type": attrs.get("type"),
            "placeholder": attrs.get("placeholder"),
            "href": attrs.get("href"),
            "value": attrs.get("value"),
            "css_path": css_path(el),
            "label": find_label_text(el) if el.name in ["input", "textarea", "select"] else None,
            "options": options,
            "multiple": el.has_attr("multiple") if el.name == "select" else False
        }

        # Drop empty noise nodes
        if record["text"] or record["id"] or record["name"]:
            elements.append(record)

    return elements