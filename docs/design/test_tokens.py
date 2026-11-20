"""Negative and positive tests for the proposed semantic token contract."""

import json
import unittest

from validate_tokens import TOKEN_FILE, contrast_ratio, validate


class DesignTokenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))

    def test_valid_design_tokens(self):
        validate(self.data)

    def test_both_themes_are_required(self):
        del self.data["color"]["dark"]
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_semantic_roles_must_match(self):
        del self.data["color"]["dark"]["onAction"]
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_text_on_surface_must_be_readable(self):
        self.data["color"]["light"]["textSecondary"] = "#DDDDDD"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_action_button_contrast(self):
        self.data["color"]["dark"]["onAction"] = self.data["color"]["dark"]["action"]
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_non_text_control_contrast(self):
        self.data["color"]["light"]["controlBorder"] = "#DDDDDD"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_invalid_color_rejected(self):
        self.data["color"]["light"]["focus"] = "rgb(0,0,0)"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_small_touch_targets_are_rejected(self):
        self.data["layout"]["minInteractiveTargetPx"] = 20
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_breakpoint_gaps_rejected(self):
        self.data["layout"]["wideMinPx"] += 30
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_boolean_is_not_an_integer_design_token(self):
        self.data["spacingPx"]["sm"] = True
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_not_production_approved_by_default(self):
        self.data["status"] = "approved"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_contrast_is_symmetric(self):
        self.assertEqual(contrast_ratio("#FFFFFF", "#000000"), 21.0)
        self.assertEqual(contrast_ratio("#000000", "#FFFFFF"), 21.0)

    def test_scale_ordering_is_enforced(self):
        self.data["typePx"]["heading"] = 13
        with self.assertRaises(ValueError):
            validate(self.data)


if __name__ == "__main__":
    unittest.main()
