from dataclasses import asdict
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.scrapers.bs4_scraper import parse_bs4_products, load_bs4_scrapers, Bs4ScraperIndex
from app.utils.product import Product
from app.utils.scrape_utils import open_browser, close_browser, reject_cookies, make_soup

def scrape_amazon(url: str) -> List[Product]:
    scrapers = load_bs4_scrapers("data/bs4_scrapers.json")  # list[Scraper]
    spec = scrapers[Bs4ScraperIndex.AMAZON]

    d, w = open_browser(12)
    try:
        d.get(url)
        reject_cookies(w, *spec.reject_cookie_ids)
        w.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, spec.item_sel)))
        soup = make_soup(d)
        return parse_bs4_products(asdict(spec), soup)  # keep old parse_products
    finally:
        close_browser(d)