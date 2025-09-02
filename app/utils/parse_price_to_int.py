import re

def parse_price_to_int(price_text: str) -> int:
    digits = re.sub(r"[^\d]", "", price_text)
    return int(digits) if digits else 0



