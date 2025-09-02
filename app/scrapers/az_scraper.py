from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC

from app.utils.product import Product
from app.utils.parse_price_to_int import parse_price_to_int

BASE = "https://www.amazon.com.tr"

def scrape_amazon(url: str, timeout: int = 12) -> List[Product]:
    out: List[Product] = []
    d = webdriver.Chrome()
    try:
        d.get(url)
        w = W(d, timeout)

        for btn_id in ("sp-cc-rejectall-link", "sp-cc-accept"):
            try:
                w.until(EC.element_to_be_clickable((By.ID, btn_id))).click()
                break
            except Exception:
                pass

        w.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.s-result-item[data-asin]")
        ))

        soup = BeautifulSoup(d.page_source, "html.parser")

        for item in soup.select("div.s-result-item[data-asin]:not([data-asin=''])"):
            if item.select_one("span.sponsored-label-text"):
                continue

            # Başlık
            title_el = item.select_one("h2 span")
            if not title_el:
                continue
            name = title_el.get_text(strip=True)

            # Fiyat
            price_el = item.select_one("span.a-price > span.a-offscreen")
            price_text = price_el.get_text(strip=True) if price_el else ""
            price_int = parse_price_to_int(price_text) if price_text else 0

            # Link
            a_el = item.select_one("h2 a[href]") or item.select_one("a.a-link-normal[href]")
            asin = item.get("data-asin", "").strip()

            if a_el:
                href = urljoin(BASE, a_el.get("href", ""))
            elif asin:
                href = f"{BASE}/dp/{asin}"
            else:
                continue

            out.append(Product(
                name=name,
                price_text=price_text,
                price=price_int,
                url=href
            ))

        return out
    finally:
        d.quit()
