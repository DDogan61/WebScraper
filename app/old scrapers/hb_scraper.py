from typing import List
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.utils.product import Product
from app.utils.price_utils import parse_price_to_int
from app.utils.scrape_utils import open_browser
from app.utils.scraper_models import SelScraper, load_sel_scrapers

SEL_SCRAPERS: list[SelScraper] = load_sel_scrapers("data/sel_scrapers.json")


def scrape_hepsiburada(site: int, url: str, timeout: int = 12) -> List[Product]:
    out: List[Product] = []
    spec = SEL_SCRAPERS[site]  # SelScraper objesi

    d, w = open_browser(timeout)   # (driver, WebDriverWait)
    try:
        d.get(url)

        # ürün kartları yüklensin
        w.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, spec.item_sel)
        ))
        cards = d.find_elements(By.CSS_SELECTOR, spec.item_sel)

        for a in cards:
            href = urljoin(spec.base_url, a.get_attribute("href") or "")
            title = (a.get_attribute(spec.title_attr) or "").strip()

            # kartın root'unu bul (opsiyonel)
            root = a
            if spec.root_xpath:
                try:
                    root = a.find_element(By.XPATH, spec.root_xpath)
                except Exception:
                    root = a

            # marka (opsiyonel)
            brand = ""
            if spec.brand_sel:
                try:
                    brand = root.find_element(By.CSS_SELECTOR, spec.brand_sel).text.strip()
                except Exception:
                    brand = ""

            # fiyat: listedeki selector'ları sırayla dene (opsiyonel liste olabilir)
            price_text = ""
            for sel in (spec.price_sel or []):
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
                    website=spec.website,
                    name=full_name,
                    price_text=price_text,
                    price=price_int,
                    url=href
                ))

        return out
    finally:
        d.quit()  # veya close_browser(d)

