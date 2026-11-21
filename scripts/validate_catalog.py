"""Validate the current Wexum planning catalog without external dependencies."""

import json
import re
from pathlib import Path


_REQUIRED_CATALOG = frozenset({"organization", "ecosystem", "hub", "products"})
_REQUIRED_HUB = frozenset({"name", "status"})
_REQUIRED_PRODUCT = frozenset({
    "id", "name", "category", "summary", "status", "standalone",
    "hub_integration", "code_owner",
})
_SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
# All 22 products and the Hub are currently planned. New lifecycle states need
# a documented schema decision before catalog producers can publish them.
_PLANNING_STATES = frozenset({"planned"})

# Reviewed, immutable pre-release product identity baseline; adding, renaming or
# repurposing IDs requires an explicit architecture decision and a reviewed
# schema change, never an incidental catalog edit.
_APPROVED_PRODUCT_IDENTITIES = {
    "vpn": "WexumVPN",
    "secure": "Wexum Secure",
    "cloud": "Wexum Cloud",
    "work": "Wexum Work",
    "plan": "Wexum Plan",
    "knowledge": "Wexum Knowledge",
    "mail": "Wexum Mail",
    "connect": "Wexum Connect",
    "create": "Wexum Create",
    "learn": "Wexum Learn",
    "translate": "Wexum Translate",
    "web": "Wexum Web",
    "publish": "Wexum Publish",
    "ai": "Wexum AI",
    "search": "Wexum Search",
    "data": "Wexum Data",
    "flow": "Wexum Flow",
    "dev": "Wexum Dev",
    "build": "Wexum Build",
    "business": "Wexum Business",
    "deploy": "Wexum Deploy",
    "personal": "Wexum Personal",
}


def _object(value: object, required: frozenset[str], location: str) -> dict:
    if type(value) is not dict:
        raise ValueError(f"{location} must be an object")
    missing = required - value.keys()
    extra = value.keys() - required
    if missing or extra:
        raise ValueError(f"{location} has missing/unsupported keys: missing={sorted(missing)}, extra={sorted(extra)}")
    return value


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{location} must be a nonempty, trimmed string")
    return value


def _planned(value: object, location: str) -> None:
    if not isinstance(value, str) or value not in _PLANNING_STATES:
        raise ValueError(f"{location} has unsupported state")


def validate_catalog(catalog: object) -> None:
    root = _object(catalog, _REQUIRED_CATALOG, "catalog")
    if root["organization"] != "IhsanSoft" or root["ecosystem"] != "Wexum":
        raise ValueError("catalog organization/ecosystem does not match Wexum")

    hub = _object(root["hub"], _REQUIRED_HUB, "hub")
    if hub["name"] != "Wexum Hub":
        raise ValueError("missing Wexum Hub")
    _planned(hub["status"], "hub.status")

    products = root["products"]
    if type(products) is not list or len(products) != 22:
        raise ValueError("expected exactly 22 products")

    seen: set[str] = set()
    for index, entry in enumerate(products):
        location = f"products[{index}]"
        product = _object(entry, _REQUIRED_PRODUCT, location)
        product_id = _text(product["id"], f"{location}.id")
        if not _SLUG.fullmatch(product_id):
            raise ValueError(f"{location}.id must be a lowercase stable slug")
        if product_id in seen:
            raise ValueError(f"duplicate product id: {product_id}")
        seen.add(product_id)

        name = _text(product["name"], f"{location}.name")
        if _APPROVED_PRODUCT_IDENTITIES.get(product_id) != name:
            raise ValueError(f"{location} has an unapproved or reassigned product identity")
        for field in ("category", "summary", "code_owner"):
            _text(product[field], f"{location}.{field}")
        if product["standalone"] is not True:
            raise ValueError(f"{location}.standalone must be boolean true")
        _planned(product["status"], f"{location}.status")
        _planned(product["hub_integration"], f"{location}.hub_integration")
    if seen != set(_APPROVED_PRODUCT_IDENTITIES):
        raise ValueError("catalog is missing approved product IDs")


def validate() -> None:
    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / "docs/catalog/products.json").read_text(encoding="utf-8"))
    validate_catalog(catalog)


if __name__ == "__main__":
    validate()
    print("Catalog contract OK")
