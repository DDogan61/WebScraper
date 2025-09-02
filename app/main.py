from typing import List

from app.utils.url_composer import load_websites, build_url
from app.utils.product import Product

from scrapers.az_scraper import scrape_amazon
from scrapers.hb_scraper import scrape_hepsiburada
from scrapers.n11_scraper import scrape_n11
from scrapers.ty_scraper import scrape_trendyol

SCRAPER_MAP = {
    "trendyol": scrape_trendyol,
    "hepsiburada": scrape_hepsiburada,
    "amazon": scrape_amazon,
    "n11": scrape_n11,
}

def get_input(prompt: str) -> List[str]:
    s = input(prompt).strip()
    return [t for t in s.split() if t]


def exclude_by_keywords(products: List[Product], bans: List[str]) -> List[Product]:
    bans_lc = [b.lower() for b in bans]
    out = []
    for p in products:
        title = (getattr(p, "name", "") or "").lower()
        if any(b in title for b in bans_lc):
            continue
        out.append(p)
    return out

def include_by_keywords(products: List[Product], keys: List[str]) -> List[Product]:
    if not keys:
        return products
    keys_cf = [k.casefold() for k in keys]
    out = []
    for p in products:
        name_cf = (p.name or "").casefold()
        if all(k in name_cf for k in keys_cf):
            out.append(p)
    return out

def collect_all_products(websites, keywords: List[str]) -> List[Product]:
    all_items: List[Product] = []
    for w in websites:
        url = build_url(w, keywords)
        scraper = SCRAPER_MAP.get(w.name.lower())
        if not scraper:
            continue

        try:
            items: List[Product] = scraper(url)
        except Exception as e:
            print(f"[{w.name}] scraper error: {e}")
            continue

        if not items:
            print(f"[{w.name}] Item not found.")
            continue

        all_items.extend(items)
    return all_items


def print_cheapest(products: List[Product], n: int = 5) -> None:
    sorted_items = sorted(
        (p for p in products if p.price > 0),
        key=lambda p: p.price
    )
    print(f"\n=== Cheapest items ===")
    for i, p in enumerate(sorted_items[:n], 1):
        print(f"{i}. {p.name} | {p.price_text} -> {p.url}")


if __name__ == "__main__":
    websites = load_websites("data/websites.json")
    keywords = get_input("Search for: ")

    all_items: List[Product] = []

    if not keywords:
        print("Empty")
    else:
        all_items = collect_all_products(websites, keywords)
        all_items = include_by_keywords(all_items, keywords)
        print(f"\nNumber of items found: {len(all_items)}")
        print_cheapest(all_items, n=5)

        while True:
            bans = get_input("\n(q/quit for quit, eliminate keywords like: keyword1 keyword2 ...): ")
            if not bans:
                print("Empty input! Try again!")
                continue
            if bans[0].lower() in ("q", "quit"):
                print("Bye!")
                break

            all_items = exclude_by_keywords(all_items, bans)
            print(f"\nAfter filtering ({', '.join(bans)}), remaining: {len(all_items)}")
            if not all_items:
                print("No items left.")
                break
            print_cheapest(all_items, n=5)