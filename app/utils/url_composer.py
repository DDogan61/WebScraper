from __future__ import annotations
from dataclasses import dataclass
from typing import List
import json
from urllib.parse import quote

from app.utils.log_config import logger


@dataclass
class Website:
    name: str
    baseUrl: str
    queryParamKeys: List[str]
    joiner: str = "+"
    extraParams: str = ""

def load_websites(path: str) -> List[Website]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Website(**item) for item in data]
    except Exception as e:
        logger.error(f"Failed to load websites from {path}: {e}", exc_info=True)
        return []

def build_url(website: Website, keywords: List[str]) -> str:
    encoded = [quote(k, safe="") for k in keywords]
    joined = website.joiner.join(encoded)

    params = "&".join(f"{key}={joined}" for key in website.queryParamKeys)

    url = f"{website.baseUrl}?{params}"
    if website.extraParams:
        url += "&" + website.extraParams.lstrip("&?")
    return url