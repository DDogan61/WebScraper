from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.utils.product import Product
from app.utils.parse_price_to_int import parse_price_to_int

BASE = "https://www.trendyol.com"

def scrape_trendyol(url: str, timeout: int = 12) -> List[Product]:
    out: List[Product] = []

    d = webdriver.Chrome()
    try:
        d.get(url)
        w = WebDriverWait(d, timeout)

        try:
            btn = w.until(EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler")))
            btn.click()
        except Exception:
            pass

        w.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.p-card-wrppr")))

        soup = BeautifulSoup(d.page_source, "html.parser")

        for item in soup.select("div.p-card-wrppr"):
            brand_el = item.select_one("span.prdct-desc-cntnr-ttl")
            name_el  = item.select_one("span.prdct-desc-cntnr-name")
            info_el  = item.select_one("div.product-desc-sub-text")
            price_el = (
                item.select_one('[data-test-id="price-current-price"]')
                or item.select_one("div.price-item.discounted")
                or item.select_one("div.prc-box-dscntd")
            )
            link_el  = item.select_one("a[href]")

            if not (name_el and price_el and link_el):
                continue

            brand = (brand_el.get_text(strip=True) if brand_el else "").strip()
            name  = name_el.get_text(strip=True)
            info  = (info_el.get_text(strip=True) if info_el else "").strip()

            full_name = " ".join(x for x in [brand, name, info] if x).strip()
            price_text = price_el.get_text(strip=True)
            price = parse_price_to_int(price_text)
            url_abs = urljoin(BASE, link_el.get("href", ""))

            out.append(Product(
                name=full_name,
                price_text=price_text,
                price=price,
                url=url_abs
            ))
        return out
    finally:
        d.quit()
