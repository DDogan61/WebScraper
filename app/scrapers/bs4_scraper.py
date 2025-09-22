from dataclasses import asdict

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.utils.log_config import logger
from app.utils.price_utils import parse_price_to_int
from app.utils.product import Product
from app.utils.scrape_utils import extract_texts, open_browser, reject_cookies, make_soup, close_browser
from app.utils.scraper_models import Bs4Scraper, load_bs4_scrapers

BS4_SCRAPERS: list[Bs4Scraper] = load_bs4_scrapers("data/bs4_scrapers.json")


def parse_bs4_products(spec: Dict[str, Any], soup: BeautifulSoup) -> List[Product]:
    out: List[Product] = []
    sponsored_sel = spec.get("sponsored_sel")
    id_attr = spec.get("id_attr")
    dp_path = spec.get("dp_path")

    for item in soup.select(spec["item_sel"]):
        if sponsored_sel and item.select_one(sponsored_sel):
            continue

        name = extract_texts(item, spec["title_sel"])
        if not name:
            continue

        price_text = ""
        price_int = 0
        for sel in spec["price_sel"]:
            price_el = item.select_one(sel)
            if price_el:
                price_text = price_el.get_text(strip=True)
                price_int = parse_price_to_int(price_text)
                break

        a_el = None
        for sel in spec["link_sel"]:
            a_el = item.select_one(sel)
            if a_el:
                break

        if a_el and a_el.has_attr("href"):
            href = urljoin(spec["base_url"], a_el["href"])
        else:
            pid = (item.get(id_attr, "").strip() if id_attr else "")
            if pid and dp_path:
                href = urljoin(spec["base_url"], dp_path.format(id=pid))
            else:
                continue

        out.append(Product(
            website=spec["website"],
            name=name,
            price_text=price_text,
            price=price_int,
            url=href
        ))

    return out


def scrape_bs4(site: int, url: str, timeout: int = 12) -> List[Product]:
    spec = BS4_SCRAPERS[site]
    d, w = open_browser(timeout)
    try:
        try:
            d.get(url)
            if spec.reject_cookie_ids:
                reject_cookies(w, *spec.reject_cookie_ids)
            w.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, spec.item_sel)))
            soup = make_soup(d)
            return parse_bs4_products(asdict(spec), soup)
        except Exception as e:
            logger.error(f"[{spec.website}] scrape_bs4 failed: {e}", exc_info=True)
            return []
    finally:
        close_browser(d)
