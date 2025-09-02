from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC

from app.utils.product import Product
from app.utils.parse_price_to_int import parse_price_to_int

BASE = "https://www.hepsiburada.com"


def scrape_hepsiburada(url: str, timeout: int = 12) -> List[Product]:
    out: List[Product] = []
    d = webdriver.Chrome()
    try:
        d.get(url)
        w = W(d, timeout)

        w.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'a[class*="productCardLink"]')
        ))
        cards = d.find_elements(By.CSS_SELECTOR, 'a[class*="productCardLink"][href]')

        for a in cards:
            href = urljoin(BASE, a.get_attribute("href") or "")
            title = (a.get_attribute("title") or "").strip()

            try:
                root = a.find_element(
                    By.XPATH,
                    './ancestor::div[contains(@class,"productCard-module_productCardRoot")][1]'
                )
            except Exception:
                root = a

            try:
                brand = root.find_element(
                    By.CSS_SELECTOR,
                    'span[class^="title-module_brandText__"]'
                ).text.strip()
            except Exception:
                brand = ""

            price_text = ""
            for sel in ('[data-test-id^="final-price"]',
                        'div[class^="price-module_finalPrice__"]'):
                try:
                    price_text = root.find_element(By.CSS_SELECTOR, sel).text.strip()
                    if price_text:
                        break
                except Exception:
                    pass

            if title or brand or price_text:
                full_name = (f"{brand} {title}").strip()
                price_int = parse_price_to_int(price_text)

                out.append(Product(
                    name=full_name,
                    price_text=price_text,
                    price=price_int,
                    url=href
                ))

        return out
    finally:
        d.quit()
