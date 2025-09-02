from typing import List
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC

from app.utils.product import Product
from app.utils.parse_price_to_int import parse_price_to_int

def scrape_n11(url: str, timeout: int = 12) -> List[Product]:
    out: List[Product] = []
    d = webdriver.Chrome()
    try:
        d.get(url)
        w = W(d, timeout)

        w.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3.productName")))

        soup = BeautifulSoup(d.page_source, "html.parser")

        titles = [t.get_text(strip=True) for t in soup.select("h3.productName")]
        prices = [p.get_text(strip=True) for p in soup.select("span.newPrice ins")]
        links  = [a["href"] for a in soup.select("a.plink[href]")]

        n = min(len(titles), len(prices), len(links))
        for i in range(n):
            title = titles[i]
            price_text = prices[i]
            url_abs = links[i]
            price_int = parse_price_to_int(price_text)

            out.append(Product(
                name=title,
                price_text=price_text,
                price=price_int,
                url=url_abs
            ))

        return out
    finally:
        d.quit()