import re

from app.utils.log_config import logger


def parse_price_to_int(price_text: str) -> int:
    try:
        digits = re.sub(r"[^\d]", "", price_text)
        return int(digits) if digits else 0
    except Exception as e:
        logger.error(f"Price parse failed for text='{price_text}': {e}", exc_info=True)
        return -1
