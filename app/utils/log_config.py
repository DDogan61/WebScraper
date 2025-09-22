import logging
from pathlib import Path

Path("logs").mkdir(exist_ok=True)

logging.getLogger("werkzeug").propagate = False

LOG_FILE = "logs/app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8", mode = "w"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("WebScraper")