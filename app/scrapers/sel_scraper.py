from typing import List
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.utils.log_config import logger
from app.utils.product import Product
from app.utils.price_utils import parse_price_to_int
from app.utils.scrape_utils import open_browser, close_browser, safe_text, safe_find, safe_first_text
from app.utils.scraper_models import SelScraper, load_sel_scrapers

SEL_SCRAPERS: list[SelScraper] = load_sel_scrapers("data/sel_scrapers.json")


def parse_sel_products(spec: SelScraper, d, w) -> List[Product]:
    out: List[Product] = []

    w.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, spec.item_sel)))
    cards = d.find_elements(By.CSS_SELECTOR, spec.item_sel)

    for a in cards:
        href = urljoin(spec.base_url, a.get_attribute("href") or "")
        title = (a.get_attribute(spec.title_attr) or "").strip()

        root = safe_find(a, By.XPATH, spec.root_xpath) if spec.root_xpath else a
        root = root or a

        brand = safe_text(root, By.CSS_SELECTOR, spec.brand_sel) if spec.brand_sel else ""
        price_text = safe_first_text(root, spec.price_sel or [])

        if not (title or brand or price_text):
            continue

        price_int = parse_price_to_int(price_text)
        if price_int == -1:
            continue

        out.append(Product(
            website=spec.website,
            name=(f"{brand} {title}").strip(),
            price_text=price_text,
            price=price_int,
            url=href
        ))

    return out


def scrape_sel(site: int, url: str, timeout: int = 12) -> List[Product]:
    spec = SEL_SCRAPERS[site]
    d, w = open_browser(timeout)
    try:
        try:
            d.get(url)
            return parse_sel_products(spec, d, w)
        except Exception as e:
            logger.error(f"[{spec.website}] scrape_sel failed: {e}", exc_info=True)
            return []
    finally:
        close_browser(d)
