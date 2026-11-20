"""Validate proposed Wexum design tokens without external dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

TOKEN_FILE = Path(__file__).with_name("tokens.json")
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_MODES = frozenset({"light", "dark"})
_COLOR_ROLES = frozenset({
    "background", "surface", "textPrimary", "textSecondary",
    "action", "onAction", "controlBorder", "focus", "danger", "success",
})


def contrast_ratio(first: str, second: str) -> float:
    """WCAG relative luminance and contrast for opaque sRGB hex colors."""
    def luminance(value: str) -> float:
        if not isinstance(value, str) or not _HEX.fullmatch(value):
            raise ValueError("expected #RRGGBB color")
        channels = (int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
        return sum(component * weight for component, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _nonnegative_scale(value: Any, *, strict: bool) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    numbers = list(value.values())
    if any(type(item) is not int or item < 0 for item in numbers):
        return False
    return all(left < right if strict else left <= right for left, right in zip(numbers, numbers[1:]))


def validate(data: dict[str, Any]) -> None:
    if data.get("status") not in ("proposed", "approved"):
        raise ValueError("token status must be proposed or approved; approval requires independent review")

    modes = data.get("color")
    if not isinstance(modes, dict) or set(modes) != _MODES:
        raise ValueError("light and dark themes are both required")

    for mode, colors in modes.items():
        if not isinstance(colors, dict) or set(colors) != _COLOR_ROLES:
            raise ValueError(f"{mode}: inconsistent semantic roles")
        if any(not isinstance(color, str) or not _HEX.fullmatch(color) for color in colors.values()):
            raise ValueError(f"{mode}: malformed color")

        for foreground in ("textPrimary", "textSecondary", "danger", "success"):
            for surface in ("background", "surface"):
                if contrast_ratio(colors[foreground], colors[surface]) < 4.5:
                    raise ValueError(f"{mode}: {foreground} fails AA contrast on {surface}")

        if contrast_ratio(colors["onAction"], colors["action"]) < 4.5:
            raise ValueError(f"{mode}: action label contrast failure")

        for role in ("controlBorder", "focus"):
            for surface in ("background", "surface"):
                if contrast_ratio(colors[role], colors[surface]) < 3:
                    raise ValueError(f"{mode}: {role} fails non-text contrast on {surface}")

    layout = data.get("layout", {})
    if not isinstance(layout, dict):
        raise ValueError("layout is missing")
    vals = [layout.get(key) for key in ("compactMaxPx", "mediumMaxPx", "wideMinPx", "minInteractiveTargetPx")]
    if any(type(v) is not int or v <= 0 for v in vals):
        raise ValueError("layout measurements must be positive integer pixels")
    if not vals[0] < vals[1] or vals[2] != vals[1] + 1 or vals[3] < 44:
        raise ValueError("layout breakpoint/target constraints violated")

    for key in ("spacingPx", "radiusPx", "typePx", "motionMs"):
        if not _nonnegative_scale(data.get(key), strict=key in ("spacingPx", "typePx", "motionMs")):
            raise ValueError(f"{key}: invalid or unsorted token scale")
    if data["typePx"]["body"] < 16:
        raise ValueError("body typography must not be undersized")

    font = data.get("font", {})
    if not isinstance(font, dict) or not all(isinstance(font.get(k), str) and font[k].strip() for k in ("latin", "arabic")):
        raise ValueError("font fallback contracts missing")


def main() -> None:
    validate(json.loads(TOKEN_FILE.read_text(encoding="utf-8")))
    print("Wexum design token contract: OK")


if __name__ == "__main__":
    main()
