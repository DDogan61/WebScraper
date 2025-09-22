import json
from dataclasses import dataclass, field
from typing import List, Optional

from app.utils.log_config import logger


@dataclass
class Bs4Scraper:
    website: str
    base_url: str
    item_sel: str
    title_sel: List[str] = field(default_factory=list)
    price_sel: List[str] = field(default_factory=list)
    link_sel: List[str] = field(default_factory=list)
    sponsored_sel: Optional[str] = None
    reject_cookie_ids: List[str] = field(default_factory=list)
    id_attr: Optional[str] = None
    dp_path: Optional[str] = None


@dataclass
class SelScraper:
    website: str
    base_url: str
    item_sel: str
    title_attr: str
    root_xpath: Optional[str] = None
    brand_sel: Optional[str] = None
    price_sel: List[str] = field(default_factory=list)


def load_bs4_scrapers(path: str) -> list[Bs4Scraper]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Bs4Scraper(**entry) for entry in data]
    except Exception as e:
        logger.error(f"Failed to load BS4 scrapers from {path}: {e}", exc_info=True)
        return []

def load_sel_scrapers(path: str) -> list[SelScraper]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [SelScraper(**entry) for entry in data]
    except Exception as e:
        logger.error(f"Failed to load SEL scrapers from {path}: {e}", exc_info=True)
        return []
