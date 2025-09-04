from typing import Tuple

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC

def open_browser(timeout: int = 12) -> Tuple[webdriver.Chrome, W]:
    d = webdriver.Chrome()
    w = W(d, timeout)
    return d, w


def close_browser(d):
    try:
        d.quit()
    except Exception:
        pass


def reject_cookies(w: W, *ids: str) -> bool:
    for btn_id in ids:
        try:
            el = w.until(EC.element_to_be_clickable((By.ID, btn_id)))
            el.click()
            return True
        except Exception:
            pass
    return False


def make_soup(d) -> BeautifulSoup:
    return BeautifulSoup(d.page_source, "html.parser")

def first_text(root, *sels):
    for s in sels:
        el = root.select_one(s)
        if el:
            txt = el.get_text(strip=True)
            if txt:
                return txt
    return ""

def first_href(root, *sels):
    for s in sels:
        el = root.select_one(s)
        if el and el.has_attr("href"):
            return el["href"].strip()
    return ""

def extract_texts(el, selectors: list[str]) -> str:
    parts = []
    for sel in selectors:
        node = el.select_one(sel)
        if node:
            txt = node.get_text(strip=True)
            if txt:
                parts.append(txt)
    return " ".join(parts).strip()
