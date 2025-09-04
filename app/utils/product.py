from dataclasses import dataclass

@dataclass
class Product:
    website: str
    name: str
    price_text: str
    price: int
    url: str