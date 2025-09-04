import csv
import io
from urllib.parse import quote

from flask import Flask, request, render_template, Response
from typing import List, Dict, Any
import time

from app.scrapers.bs4_scraper import scrape_trendyol, scrape_amazon, scrape_n11
from app.scrapers.sel_scraper import scrape_hepsiburada
from app.utils.url_composer import load_websites, build_url
from app.utils.product import Product

SCRAPER_MAP = {
    "trendyol": scrape_trendyol,
    "hepsiburada": scrape_hepsiburada,
    "amazon": scrape_amazon,
    "n11": scrape_n11,
}

app = Flask(__name__)
WEBSITES = load_websites("data/websites.json")

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
        if all(k in name_cf for k in keys_cf):  # AND
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

# --------------- scrape ----------------
def collect_all_products(websites, keywords: List[str]) -> List[Product]:
    all_items: List[Product] = []
    for w in websites:
        url = build_url(w, keywords)
        scraper = SCRAPER_MAP.get(w.name.lower())
        if not scraper: continue
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

def filter_by_sites(items, allowed_sites: set[str]):
    if not allowed_sites:
        return []
    out = []
    for p in items:
        if p.website in allowed_sites:
            out.append(p)
    return out

@app.get("/export")
def export_csv():
    query   = request.args.get("q", "").strip()
    ban_str = request.args.get("ban", "").strip()
    refresh = request.args.get("refresh", "0") == "1"

    if not query:
        return Response("Missing q", status=400)

    # site selection
    all_sites = [w.name.lower() for w in WEBSITES]
    user_touched_sites = request.args.get("site_sel") == "1"
    selected_sites = request.args.getlist("site") if user_touched_sites else all_sites
    selected_set = set(s.lower() for s in selected_sites)

    # filter items (no top-5 limit)
    keywords = query.split()
    bans     = ban_str.split() if ban_str else []

    items = None if refresh else cache_get(query)
    if items is None:
        items = collect_all_products(WEBSITES, keywords)
        items = include_by_keywords(items, keywords)
        cache_set(query, items)

    items = filter_by_sites(items, selected_set)
    items = exclude_by_keywords(items, bans)
    items = sorted((p for p in items if p.price > 0), key=lambda p: p.price)

    # ---- CSV for Excel TR: use semicolon + UTF-8 BOM + CRLF ----
    sio = io.StringIO(newline="")
    sio.write("\ufeff")  # BOM so Excel opens UTF-8 correctly
    writer = csv.writer(
        sio,
        delimiter=";",           # IMPORTANT: semicolon for Excel in TR locales
        lineterminator="\r\n",   # Windows-friendly newlines
        quoting=csv.QUOTE_MINIMAL
    )

    writer.writerow(["#", "Name", "Price", "Website", "URL"])
    for idx, p in enumerate(items, start=1):
        writer.writerow([idx, p.name, p.price_text, p.website, p.url])

    filename = f"export_{quote(query)}.csv"
    return Response(
        sio.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --------------- route ----------------
@app.get("/")
def home():
    query   = request.args.get("q", "").strip()
    ban_str = request.args.get("ban", "").strip()
    refresh = request.args.get("refresh", "0") == "1"

    keywords = query.split() if query else []
    bans     = ban_str.split() if ban_str else []

    if not keywords:
        return render_template("home.html")

    # 1) Önce cache’e bak (aynı query için)
    items = None if refresh else cache_get(query)

    # 2) Cache yoksa (veya refresh istendiyse) sadece bu aşamada scrape et
    if items is None:
        items = collect_all_products(WEBSITES, keywords)
        items = include_by_keywords(items, keywords)
        # cache’e ham listeyi (ban uygulanmadan önceki hali) koy
        cache_set(query, items)

    # 3) Sitelere göre eleme yap.
    all_sites = [w.name.lower() for w in WEBSITES]
    user_touched_sites = request.args.get("site_sel") == "1"

    if user_touched_sites:
        selected_sites = request.args.getlist("site")  # intentionally can be []
    else:
        selected_sites = all_sites

    selected_set = set(s.lower() for s in selected_sites)

    # 4) Filtreleri uygula
    items = filter_by_sites(items, selected_set)
    items = exclude_by_keywords(items, bans)

    filtered = sorted((p for p in items if p.price > 0), key=lambda p: p.price)[:5]

    data = [{"website":p.website, "name": p.name, "price_text": p.price_text, "price": p.price, "url": p.url} for p in filtered]
    return render_template("home.html", query=query, ban=ban_str, results=data, selected_sites=selected_set)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
