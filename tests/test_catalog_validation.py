"""Catalog contract negative tests (no external dependencies)."""

import unittest
from json import loads
from pathlib import Path

from scripts.validate_catalog import validate_catalog


def planned_catalog():
    """Fresh mutable copy of the approved 22-product catalog fixture."""
    root = Path(__file__).resolve().parents[1]
    return loads((root / "docs/catalog/products.json").read_text(encoding="utf-8"))


class CatalogValidationTests(unittest.TestCase):
    def test_repository_catalog_is_valid(self):
        root = Path(__file__).resolve().parents[1]
        catalog = loads((root / "docs/catalog/products.json").read_text(encoding="utf-8"))
        validate_catalog(catalog)

    def test_valid_planning_catalog(self):
        catalog = planned_catalog()
        catalog["products"].reverse()  # Reordering catalog entries is compatible.
        validate_catalog(catalog)

    def test_bad_ids_are_rejected(self):
        for invalid in ("", " ", "VPN", "bad/id", "_vpn", None, 99, []):
            with self.subTest(invalid=invalid):
                catalog = planned_catalog()
                catalog["products"][0]["id"] = invalid
                with self.assertRaises(ValueError):
                    validate_catalog(catalog)

    def test_duplicate_id_is_rejected(self):
        catalog = planned_catalog()
        catalog["products"][0]["id"] = catalog["products"][1]["id"]
        with self.assertRaises(ValueError):
            validate_catalog(catalog)

    def test_existing_product_id_cannot_be_renamed(self):
        catalog = planned_catalog()
        catalog["products"][0]["id"] = "renamed-product"
        with self.assertRaises(ValueError):
            validate_catalog(catalog)

    def test_existing_product_ids_cannot_be_swapped(self):
        catalog = planned_catalog()
        first, second = catalog["products"][:2]
        first["id"], second["id"] = second["id"], first["id"]
        with self.assertRaises(ValueError):
            validate_catalog(catalog)

    def test_non_identity_metadata_can_change(self):
        catalog = planned_catalog()
        catalog["products"][0]["summary"] = "Updated planning description"
        validate_catalog(catalog)

    def test_invalid_lifecycle_states_are_rejected(self):
        for field in ("status", "hub_integration"):
            for invalid in ("published", "active", "unknown", "", None, [], 0):
                with self.subTest(field=field, invalid=invalid):
                    catalog = planned_catalog()
                    catalog["products"][0][field] = invalid
                    with self.assertRaises(ValueError):
                        validate_catalog(catalog)
        catalog = planned_catalog()
        catalog["hub"]["status"] = "unknown"
        with self.assertRaises(ValueError):
            validate_catalog(catalog)

    def test_boolean_and_required_metadata_are_checked(self):
        for invalid in (1, "true", False, None):
            with self.subTest(invalid=invalid):
                catalog = planned_catalog()
                catalog["products"][0]["standalone"] = invalid
                with self.assertRaises(ValueError):
                    validate_catalog(catalog)
        for field in ("name", "category", "summary", "code_owner"):
            with self.subTest(field=field):
                catalog = planned_catalog()
                catalog["products"][0][field] = " "
                with self.assertRaises(ValueError):
                    validate_catalog(catalog)

    def test_missing_or_unrecognized_keys_are_checked(self):
        for target in ("catalog", "hub", "product"):
            with self.subTest(target=target):
                catalog = planned_catalog()
                if target == "catalog":
                    del catalog["organization"]
                elif target == "hub":
                    catalog["hub"]["unsupported"] = True
                else:
                    del catalog["products"][0]["summary"]
                with self.assertRaises(ValueError):
                    validate_catalog(catalog)

    def test_invalid_root_and_product_collections_are_checked(self):
        for invalid in (None, [], "catalog"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate_catalog(invalid)
        for invalid in ("not-list", [], {}, [None] * 22):
            with self.subTest(invalid=invalid):
                catalog = planned_catalog()
                catalog["products"] = invalid
                with self.assertRaises(ValueError):
                    validate_catalog(catalog)

    def test_org_identity_and_hub_are_checked(self):
        catalog = planned_catalog()
        catalog["organization"] = "Other"
        with self.assertRaises(ValueError):
            validate_catalog(catalog)
        catalog = planned_catalog()
        catalog["hub"]["name"] = "Other Hub"
        with self.assertRaises(ValueError):
            validate_catalog(catalog)


if __name__ == "__main__":
    unittest.main()
