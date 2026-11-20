"""Validation and lookup of planned Wexum internationalization metadata.

No locale in this registry is considered shipped merely because it is listed.
"""

import json
import re
from pathlib import Path

REGISTRY_FILE = Path(__file__).with_name("locales.json")
TAG = re.compile(r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})$")
TIERS = {"priority", "growth", "later"}
DIRECTIONS = {"ltr", "rtl"}
RTL_REVIEWED = {"ar-SA", "ar-EG", "ar-MA", "ar-AE", "ur-PK", "fa-IR", "he-IL",
                "ps-AF", "pa-Arab-PK", "ckb-IQ", "ug-CN", "dv-MV"}


def load_registry() -> dict:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def validate_registry(data: dict) -> None:
    if data.get("schema") != 1 or data.get("defaultLocale") != "en-US":
        raise ValueError("unexpected schema or default locale")
    entries = data.get("locales")
    if not isinstance(entries, list) or not entries:
        raise ValueError("locale catalog missing")
    tags: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("invalid locale entry")
        tag = entry.get("tag")
        if not isinstance(tag, str) or not TAG.fullmatch(tag):
            raise ValueError("noncanonical or unsupported locale tag")
        if tag in tags:
            raise ValueError("duplicate locale")
        if not isinstance(entry.get("nameEnglish"), str) or not entry["nameEnglish"].strip():
            raise ValueError("missing locale name")
        if entry.get("direction") not in DIRECTIONS or entry["direction"] != ("rtl" if tag in RTL_REVIEWED else "ltr"):
            raise ValueError("direction requires reviewed script metadata")
        if entry.get("tier") not in TIERS or entry.get("translationStatus") != "planned":
            raise ValueError("unreviewed translations cannot be marked shipped")
        tags[tag] = entry

    if data["defaultLocale"] not in tags or tags["en-US"].get("fallback") is not None:
        raise ValueError("invalid root fallback")

    for tag, entry in tags.items():
        fallback = entry.get("fallback")
        if tag != "en-US" and (fallback is None or fallback not in tags or fallback == tag):
            raise ValueError("invalid fallback")
        traversed = set()
        current = tag
        while current is not None:
            if current in traversed:
                raise ValueError("circular fallback")
            traversed.add(current)
            current = tags[current].get("fallback")
        if "en-US" not in traversed:
            raise ValueError("fallback must reach default locale")

    for group in ("languageDefaults", "scriptDefaults"):
        mappings = data.get(group)
        if not isinstance(mappings, dict):
            raise ValueError("missing locale default mappings")
        for key, target in mappings.items():
            if not isinstance(key, str) or not key or target not in tags:
                raise ValueError("invalid default mapping")
            if group == "languageDefaults" and (not re.fullmatch(r"[a-z]{2,3}", key) or not target.startswith(key + "-")):
                raise ValueError("language mapping does not match target")
            if group == "scriptDefaults" and (not re.fullmatch(r"[a-z]{2,3}-[A-Z][a-z]{3}", key) or not target.startswith(key + "-")):
                raise ValueError("script mapping does not match target")


def resolve_locale(preferred: str | None, published: set[str], data: dict) -> str | None:
    """Resolve only to a locale with a separately verified, published catalog.

    The caller supplies published locales from an approved release inventory,
    never directly from client-controlled input. None means there is no available UI catalog.
    """
    entries = {entry["tag"]: entry for entry in data["locales"]}
    if not published or not isinstance(preferred, str):
        return data["defaultLocale"] if data["defaultLocale"] in published else None

    by_lower = {tag.lower(): tag for tag in entries}
    canonical = by_lower.get(preferred.lower())
    subtags = preferred.split("-")
    if canonical is None and len(subtags) >= 2:
        canonical = data["scriptDefaults"].get(f"{subtags[0].lower()}-{subtags[1].title()}")
    if canonical is None:
        canonical = data["languageDefaults"].get(subtags[0].lower(), data["defaultLocale"])

    current = canonical
    while current is not None:
        if current in published:
            return current
        current = entries[current]["fallback"]
    return None


def main() -> None:
    data = load_registry()
    validate_registry(data)
    print(f"Locale plan valid: {len(data['locales'])} entries; no translations marked released")


if __name__ == "__main__":
    main()
