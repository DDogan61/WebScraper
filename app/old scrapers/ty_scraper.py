from dataclasses import asdict
from typing import List
from selenium.webdriver.support import expected_conditions as EC

from app.scrapers.bs4_scraper import parse_bs4_products, Bs4ScraperIndex, load_bs4_scrapers
from app.utils.product import Product

from selenium.webdriver.common.by import By

from app.utils.scrape_utils import reject_cookies, make_soup, close_browser, open_browser

def scrape_trendyol(url: str) -> List[Product]:
    scrapers = load_bs4_scrapers("data/bs4_scrapers.json")
    spec = scrapers[Bs4ScraperIndex.TRENDYOL]

    d, w = open_browser(12)
    try:
        d.get(url)
        w.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, spec.item_sel)))
        soup = make_soup(d)
        return parse_bs4_products(asdict(spec), soup)
    finally:
        close_browser(d)
