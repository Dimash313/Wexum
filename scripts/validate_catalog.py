"""Validate stable product identities without installing dependencies."""

from json import loads
from pathlib import Path


def validate() -> None:
    root = Path(__file__).resolve().parents[1]
    catalog = loads((root / "docs/catalog/products.json").read_text(encoding="utf-8"))
    products = catalog["products"]
    ids = [p["id"] for p in products]
    if len(ids) != 22 or len(set(ids)) != len(ids):
        raise ValueError("expected exactly 22 distinct product IDs")
    if any(not p["name"].startswith("Wexum") or not p["standalone"] for p in products):
        raise ValueError("invalid product identity or standalone contract")
    if catalog["hub"]["name"] != "Wexum Hub":
        raise ValueError("missing integration Hub")


if __name__ == "__main__":
    validate()
    print("Catalog contract OK")

