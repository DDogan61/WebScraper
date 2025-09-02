from dataclasses import dataclass

@dataclass
class Product:
    name: str
    price_text: str
    price: int
    url: str