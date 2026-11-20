"""Registry validation and fallback isolation tests."""

import copy
import unittest
from validate_locales import load_registry, resolve_locale, validate_registry


class InternationalizationTests(unittest.TestCase):
    def setUp(self):
        self.data = load_registry()

    def test_catalog_is_valid(self):
        validate_registry(self.data)

    def test_catalog_has_102_planned_locales(self):
        self.assertEqual(len(self.data["locales"]), 102)
        self.assertEqual(len({x["tag"].split("-")[0] for x in self.data["locales"]}), 81)
        self.assertTrue(all(x["translationStatus"] == "planned" for x in self.data["locales"]))

    def test_all_locales_have_a_fallback_to_default(self):
        entries = {x["tag"]: x for x in self.data["locales"]}
        for locale in entries:
            seen = set()
            while locale is not None:
                self.assertNotIn(locale, seen)
                seen.add(locale)
                locale = entries[locale]["fallback"]
            self.assertIn("en-US", seen)

    def test_duplicate_language_tag_is_rejected(self):
        self.data["locales"].append(copy.deepcopy(self.data["locales"][0]))
        with self.assertRaises(ValueError):
            validate_registry(self.data)

    def test_wrong_direction_is_rejected(self):
        for locale in self.data["locales"]:
            if locale["tag"] == "ur-PK":
                locale["direction"] = "ltr"
        with self.assertRaises(ValueError):
            validate_registry(self.data)

    def test_cyclic_fallback_is_rejected(self):
        for locale in self.data["locales"]:
            if locale["tag"] == "es-ES":
                locale["fallback"] = "es-MX"
        with self.assertRaises(ValueError):
            validate_registry(self.data)

    def test_false_published_claim_is_rejected(self):
        self.data["locales"][1]["translationStatus"] = "available"
        with self.assertRaises(ValueError):
            validate_registry(self.data)

    def test_invalid_tag_is_rejected(self):
        self.data["locales"][0]["tag"] = "English_US"
        with self.assertRaises(ValueError):
            validate_registry(self.data)

    def test_resolves_only_published_locales(self):
        self.assertIsNone(resolve_locale("es-MX", set(), self.data))
        self.assertEqual(resolve_locale("es-MX", {"en-US"}, self.data), "en-US")
        self.assertEqual(resolve_locale("es-MX", {"en-US", "es-ES"}, self.data), "es-ES")
        self.assertEqual(resolve_locale("es-MX", {"en-US", "es-ES", "es-MX"}, self.data), "es-MX")

    def test_script_direction_does_not_fall_back_to_different_chinese_script(self):
        self.assertEqual(resolve_locale("zh-Hant-HK", {"en-US", "zh-Hans-CN", "zh-Hant-TW"}, self.data), "zh-Hant-TW")
        self.assertEqual(resolve_locale("zh-Hant-TW", {"en-US", "zh-Hans-CN"}, self.data), "en-US")

    def test_unknown_locale_uses_available_fallback(self):
        self.assertEqual(resolve_locale("xx-YY", {"en-US"}, self.data), "en-US")
        self.assertIsNone(resolve_locale("xx-YY", set(), self.data))

    def test_language_only_preference(self):
        self.assertEqual(resolve_locale("es", {"en-US", "es-ES"}, self.data), "es-ES")

    def test_malformed_mapping_is_rejected(self):
        self.data["scriptDefaults"]["zh-Hant"] = "zh-Hans-CN"
        with self.assertRaises(ValueError):
            validate_registry(self.data)


if __name__ == "__main__":
    unittest.main()
