"""Dependency-free regression tests for proposed store metadata, not publication tests."""

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from validate_metadata import (
    is_public_https,
    release_preflight,
    utf16_units,
    validate_manifest,
    valid_media_path,
)

HERE = Path(__file__).parent
UI_LOCALES = {'en-US', 'es-ES', 'ru-RU', 'ar-SA'}
SAMPLE = json.loads((HERE / 'examples/wexumvpn-drafts.json').read_text(encoding='utf-8'))


class StorefrontMetadataTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(SAMPLE)

    def check(self):
        return validate_manifest(self.data, UI_LOCALES)

    def test_sample_has_eight_valid_draft_localizations(self):
        self.assertEqual(len(self.data['listings']), 8)
        self.assertEqual(self.check(), [])
        self.assertEqual(self.data['publicationStatus'], 'draft')

    def test_draft_is_not_publishable(self):
        with tempfile.TemporaryDirectory() as folder:
            issues = release_preflight(self.data, UI_LOCALES, Path(folder))
        self.assertTrue(any('independently reviewed' in msg for msg in issues))

    def test_no_publish_state_in_source_manifest(self):
        self.data['publicationStatus'] = 'published'
        self.assertIn('draft-only', str(self.check()))

    def test_no_publish_state_in_listing(self):
        self.data['listings'][0]['status'] = 'published'
        self.assertIn('no published state', str(self.check()))

    def test_malformed_status_does_not_crash_validator(self):
        self.data['listings'][0]['status'] = []
        self.assertIn('no published state', str(self.check()))

    def test_invalid_product_identifier(self):
        self.data['product'] = '../different'
        self.assertIn('Invalid product', str(self.check()))

    def test_missing_or_duplicate_listings(self):
        self.data['listings'] = []
        self.assertIn('nonempty', str(self.check()))
        self.data['listings'] = [copy.deepcopy(SAMPLE['listings'][0])] * 2
        self.assertIn('duplicate store/locale', str(self.check()))

    def test_unknown_ui_locale_is_rejected(self):
        self.data['listings'][0]['uiLocale'] = 'xx-YY'
        self.assertIn('not in planned', str(self.check()))

    def test_malformed_locale_tag_is_rejected(self):
        self.data['listings'][0]['storeLocale'] = 'english_US'
        self.assertIn('invalid storeLocale', str(self.check()))

    def test_unknown_platform_is_rejected(self):
        self.data['listings'][0]['store'] = 'random-app-store'
        self.assertIn('invalid store', str(self.check()))
        self.data['listings'][0]['store'] = []
        self.assertIn('invalid store', str(self.check()))

    def test_apple_name_minimum_two_characters(self):
        self.data['listings'][4]['metadata']['name'] = 'W'
        self.assertIn('Apple name must be at least two', str(self.check()))

    def test_play_name_limit_30_utf16_units(self):
        self.data['listings'][0]['metadata']['title'] = '界' * 30
        self.assertEqual(self.check(), [])
        self.data['listings'][0]['metadata']['title'] += '界'
        self.assertIn('title exceeds 30', str(self.check()))

    def test_play_short_description_limit_80(self):
        self.data['listings'][0]['metadata']['shortDescription'] = 'a' * 80
        self.assertEqual(self.check(), [])
        self.data['listings'][0]['metadata']['shortDescription'] += 'a'
        self.assertIn('shortDescription exceeds 80', str(self.check()))

    def test_play_long_description_limit_4000(self):
        self.data['listings'][0]['metadata']['fullDescription'] = 'a' * 4000
        self.assertEqual(self.check(), [])
        self.data['listings'][0]['metadata']['fullDescription'] += 'a'
        self.assertIn('fullDescription exceeds 4000', str(self.check()))

    def test_apple_name_and_subtitle_limits(self):
        apple = self.data['listings'][4]
        apple['metadata']['name'] = 'a' * 31
        apple['metadata']['subtitle'] = 's' * 31
        issues = self.check()
        self.assertIn('name exceeds 30', str(issues))
        self.assertIn('subtitle exceeds 30', str(issues))

    def test_apple_description_limit(self):
        apple = self.data['listings'][4]
        apple['metadata']['description'] = 'a' * 4001
        self.assertIn('description exceeds 4000', str(self.check()))

    def test_apple_promotional_text_limit(self):
        apple = self.data['listings'][4]
        apple['metadata']['promotionalText'] = 'z' * 170
        self.assertEqual(self.check(), [])
        apple['metadata']['promotionalText'] += 'z'
        self.assertIn('promotionalText exceeds 170', str(self.check()))

    def test_apple_keyword_limit_is_bytes_not_characters(self):
        apple = self.data['listings'][4]
        apple['metadata']['keywords'] = ','.join(['арабский' * 4] * 2)
        self.assertIn('100 UTF-8 bytes', str(self.check()))
        self.assertEqual(len('русский'.encode('utf-8')), 14)

    def test_apple_keywords_require_long_enough_distinct_terms(self):
        apple = self.data['listings'][4]
        apple['metadata']['keywords'] = 'ab,abcd,abcd'
        self.assertIn('distinct words longer', str(self.check()))

    def test_no_unknown_or_missing_platform_metadata_fields(self):
        item = self.data['listings'][0]['metadata']
        item['extraKeywords'] = 'something'
        self.assertIn('unexpected metadata', str(self.check()))
        del item['extraKeywords']
        del item['title']
        self.assertIn('missing required', str(self.check()))

    def test_no_html_description(self):
        self.data['listings'][4]['metadata']['description'] = '<b>best</b>'
        self.assertIn('cannot include HTML', str(self.check()))

    def test_control_characters_and_surrogates_are_rejected(self):
        self.data['listings'][4]['metadata']['name'] = 'BAD\x01NAME'
        self.assertIn('control characters', str(self.check()))
        self.data['listings'][4]['metadata']['name'] = 'BAD\ud800NAME'
        self.assertIn('control characters', str(self.check()))

    def test_emoji_counts_as_two_utf16_units_conservatively(self):
        self.assertEqual(utf16_units('🙂'), 2)
        self.data['listings'][0]['metadata']['title'] = '🙂' * 16
        self.assertIn('title exceeds 30', str(self.check()))

    def test_bad_screenshot_paths_are_rejected(self):
        for value in ['/etc/passwd.png', 'assets/../secret.png', 'assets\\secret.png', 'marketing/banner.png']:
            with self.subTest(value=value):
                self.assertFalse(valid_media_path(value))
        item = self.data['listings'][0]
        item['screenshots'] = [{'path': '../secret.png', 'sha256': 'a' * 64}]
        self.assertIn('invalid asset path', str(self.check()))

    def test_screenshot_entries_require_sha256_and_uniqueness(self):
        item = self.data['listings'][0]
        item['screenshots'] = [{'path': 'assets/en/one.png', 'sha256': 'xyz'}]
        self.assertIn('invalid asset path/hash', str(self.check()))
        item['screenshots'] = [{'path': 'assets/en/one.png', 'sha256': 'a' * 64}] * 2
        self.assertIn('duplicate screenshot', str(self.check()))

    def test_https_urls_and_private_addresses_are_conservatively_rejected(self):
        self.assertTrue(is_public_https('https://support.ihsansoft.com/help'))
        for url in ['http://support.ihsansoft.com', 'https://example.com',
                    'https://127.0.0.1/private', 'https://user:password@public.org/a',
                    'https://support.localhost/private', 'https://good.org:444/private',
                    'https://good.org/path#fragment']:
            with self.subTest(url=url):
                self.assertFalse(is_public_https(url))

    def test_release_requires_all_human_review_and_links(self):
        listing = self.data['listings'][0]
        listing['status'] = 'reviewed'
        with tempfile.TemporaryDirectory() as folder:
            issues = release_preflight(self.data, UI_LOCALES, Path(folder))
        self.assertIn('missing translationReviewer', str(issues))
        self.assertIn('store locale short code', str(issues))
        self.assertIn('at least two real localized screenshots', str(issues))
        self.assertIn('HTTPS privacy and support URLs', str(issues))
        self.assertIn('contact email', str(issues))

    def _positive_preflight_fixture(self, folder: Path):
        self.data['listings'] = [copy.deepcopy(self.data['listings'][0])]
        listing = self.data['listings'][0]
        listing['status'] = 'reviewed'
        listing['review'] = {
            'translationReviewer': 'locale-human-review-id',
            'claimsReviewer': 'product-acceptance-review-id',
            'assetsReviewer': 'screenshot-review-id',
            'privacyLegalReviewer': 'legal-review-id',
            'ethicalReviewer': 'ethical-review-id',
            'localeReviewer': 'store-locale-review-id',
            'featureEvidence': 'product-build-review-id',
            'storeLocaleSource': 'https://support.google.com/googleplay/android-developer/answer/9844778',
        }
        listing['storeContact'] = {
            'privacyPolicyUrl': 'https://example-ihsansoft.org/privacy',
            'supportUrl': 'https://example-ihsansoft.org/support',
            'supportEmail': 'support@example-ihsansoft.org',
        }
        assets = folder / 'assets/en'
        assets.mkdir(parents=True)
        listing['screenshots'] = []
        for index in (1, 2):
            target = assets / f'{index}.png'
            target.write_bytes(b'\x89PNG\r\n\x1a\n' + bytes([index]))
            listing['screenshots'].append({
                'path': 'assets/en/' + target.name,
                'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            })
        return listing

    def test_positive_evidence_preflight_is_not_a_publish_action(self):
        with tempfile.TemporaryDirectory() as folder:
            self._positive_preflight_fixture(Path(folder))
            self.assertEqual(release_preflight(self.data, UI_LOCALES, Path(folder)), [])

    def test_screenshot_hash_mismatch_blocks_preflight(self):
        with tempfile.TemporaryDirectory() as folder:
            item = self._positive_preflight_fixture(Path(folder))
            item['screenshots'][0]['sha256'] = '0' * 64
            self.assertIn('checksum mismatch', str(release_preflight(self.data, UI_LOCALES, Path(folder))))

    def test_symlink_image_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            item = self._positive_preflight_fixture(Path(folder))
            target = Path(folder) / item['screenshots'][0]['path']
            old = target.with_suffix('.old')
            target.rename(old)
            target.symlink_to(old)
            self.assertIn('symlink screenshot', str(release_preflight(self.data, UI_LOCALES, Path(folder))))

    def test_outside_symlink_directory_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as outside:
            item = self._positive_preflight_fixture(Path(folder))
            src = Path(folder) / item['screenshots'][0]['path']
            external = Path(outside) / 'capture.png'
            external.write_bytes(src.read_bytes())
            src.unlink()
            src.symlink_to(external)
            self.assertIn('unsafe screenshot', str(release_preflight(self.data, UI_LOCALES, Path(folder))))

    def test_preflight_does_not_publish_or_contact_stores(self):
        with tempfile.TemporaryDirectory() as folder:
            self._positive_preflight_fixture(Path(folder))
            self.assertEqual(release_preflight(self.data, UI_LOCALES, Path(folder)), [])
            self.assertEqual(self.data['publicationStatus'], 'draft')


if __name__ == '__main__':
    unittest.main()
