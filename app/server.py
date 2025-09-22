import csv
import io
from urllib.parse import quote

from flask import Flask, request, render_template, Response
from typing import List, Dict, Any
import time

from app.scrapers.bs4_scraper import scrape_bs4
from app.scrapers.sel_scraper import scrape_sel
from app.utils.url_composer import load_websites, build_url
from app.utils.product import Product

from app.utils.log_config import logger

app = Flask(__name__)
WEBSITES = load_websites("data/websites.json")

SCRAPER_MAP = {
    "trendyol": {"func": scrape_bs4, "index": 0},
    "hepsiburada": {"func": scrape_sel, "index": 0},
    "amazon": {"func": scrape_bs4, "index": 1},
    "n11": {"func": scrape_bs4, "index": 2},
}

# ---- CACHE ----
CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_MAX_KEYS = 30


def cache_get(query: str):
    ent = CACHE.get(query)
    if not ent:
        return None
    return ent["data"]


def cache_set(query: str, items: List[Product]) -> None:
    if len(CACHE) >= CACHE_MAX_KEYS:
        oldest_key = min(CACHE, key=lambda k: CACHE[k]["ts"])
        CACHE.pop(oldest_key, None)
    CACHE[query] = {"ts": time.time(), "data": items}


# --------------- filters ----------------
def include_by_keywords(products: List[Product], keys: List[str]) -> List[Product]:
    if not keys: return products
    keys_cf = [k.casefold() for k in keys]
    out: List[Product] = []
    for p in products:
        name_cf = (p.name or "").casefold()
        if all(k in name_cf for k in keys_cf):
            out.append(p)
    return out


def exclude_by_keywords(products: List[Product], bans: List[str]) -> List[Product]:
    if not bans: return products
    bans_cf = [b.casefold() for b in bans]
    out: List[Product] = []
    for p in products:
        name_cf = (p.name or "").casefold()
        if any(b in name_cf for b in bans_cf):
            continue
        out.append(p)
    return out


def filter_by_sites(items, allowed_sites: set[str]):
    if not allowed_sites:
        return []
    out = []
    for p in items:
        if p.website in allowed_sites:
            out.append(p)
    return out


# --------------- scrape ----------------
def collect_all_products(websites, keywords: List[str]) -> List[Product]:
    all_items: List[Product] = []
    for w in websites:
        url = build_url(w, keywords)
        entry = SCRAPER_MAP.get(w.name.lower())
        if not entry:
            logger.error(f"[{w.name}] No scraper entry found in SCRAPER_MAP")
            continue

        func, idx = entry["func"], entry["index"]

        try:
            items: List[Product] = func(idx, url)
        except Exception as e:
            logger.error(f"[{w.name}] Scraper execution failed: {e}", exc_info=True)
            continue

        if not items:
            logger.warning(f"[{w.name}] No items found.")
            continue

        all_items.extend(items)
    return all_items


def parse_request_params():
    query   = request.args.get("q", "").strip()
    ban_str = request.args.get("ban", "").strip()
    refresh = request.args.get("refresh", "0") == "1"

    keywords = query.split() if query else []
    bans     = ban_str.split() if ban_str else []

    all_sites = [w.name.lower() for w in WEBSITES]
    user_touched = request.args.get("site_sel") == "1"
    selected = request.args.getlist("site") if user_touched else all_sites
    selected_set = set(s.lower() for s in selected)

    return query, ban_str, keywords, bans, refresh, selected_set


def get_items_for_query(query: str, keywords, refresh: bool) -> List[Product]:
    items = None if refresh else cache_get(query)
    if items is None:
        items = collect_all_products(WEBSITES, keywords)
        items = include_by_keywords(items, keywords)
        cache_set(query, items)
    return items


@app.get("/export")
def export_csv():
    query, ban_str, keywords, bans, refresh, selected_set = parse_request_params()
    if not query:
        return Response("Missing q", status=400)

    items = get_items_for_query(query, keywords, refresh)
    items = filter_by_sites(items, selected_set)
    items = exclude_by_keywords(items, bans)
    items = sorted((p for p in items if p.price > 0), key=lambda p: p.price)

    # ---- Excel TR için CSV ----
    sio = io.StringIO(newline="")
    sio.write("\ufeff")  # BOM, bu sayede UTF-8 doğru açılır
    writer = csv.writer(
        sio,
        delimiter=";",  # Excel TR için semicolon
        lineterminator="\r\n",  # Windows için yeni line
        quoting=csv.QUOTE_MINIMAL
    )

    writer.writerow(["#", "Name", "Price", "Website", "URL"])
    for idx, p in enumerate(items, start=1):
        writer.writerow([idx, p.name, p.price_text, p.website, p.url])

    filename = f"export_{quote(query)}.csv"
    try:
        return Response(
            sio.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error(f"Export failed for query='{query}': {e}", exc_info=True)
        return Response("Internal server error", status=500)


# --------------- route ----------------
@app.get("/")
def home():
    query, ban_str, keywords, bans, refresh, selected_set = parse_request_params()
    if not keywords:
        return render_template("home.html")

    items = get_items_for_query(query, keywords, refresh)
    items = filter_by_sites(items, selected_set)
    items = exclude_by_keywords(items, bans)
    filtered = sorted((p for p in items if p.price > 0), key=lambda p: p.price)[:5]

    data = [{"website": p.website, "name": p.name, "price_text": p.price_text, "price": p.price, "url": p.url} for p in
            filtered]
    return render_template("home.html", query=query, ban=ban_str, results=data, selected_sites=selected_set)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
