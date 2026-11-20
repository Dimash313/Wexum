"""Conservative preflight for proposed Wexum store listing copy.

This module does not access storefront accounts or publish listings.
Vendor UI/locales/policies require manual verification before each release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import ipaddress
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

STORES = {'google-play', 'app-store'}
TAG = re.compile(r'^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-(?:[A-Z]{2}|[0-9]{3}))?$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')
APPROVAL_FIELDS = ('translationReviewer', 'claimsReviewer', 'assetsReviewer',
                   'privacyLegalReviewer', 'ethicalReviewer', 'localeReviewer', 'featureEvidence')
GOOGLE_FIELDS = {'title', 'shortDescription', 'fullDescription'}
APPLE_FIELDS = {'name', 'subtitle', 'description', 'keywords', 'promotionalText'}
APPROVED_STATUS = {'draft', 'reviewed'}
GOOGLE_LENGTHS = {'title': 30, 'shortDescription': 80, 'fullDescription': 4000}
APPLE_LENGTHS = {'name': 30, 'subtitle': 30, 'description': 4000, 'promotionalText': 170}


def utf16_units(text: str) -> int:
    """Conservative field length proxy; actual storefront counters may differ."""
    return len(text.encode('utf-16-le', errors='surrogatepass')) // 2


def is_public_https(value: object) -> bool:
    if not isinstance(value, str) or len(value) > 2048 or any(ch.isspace() for ch in value):
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        if not (parsed.scheme == 'https' and host and '.' in host and
                not parsed.username and not parsed.password and not parsed.fragment and
                parsed.port in {None, 443}):
            return False
        if host in {'example.com', 'example.org', 'example.net'} or host.endswith(('.example', '.test', '.invalid', '.localhost', '.local')):
            return False
        try:
            ipaddress.ip_address(host)
            return False
        except ValueError:
            return True
    except ValueError:
        return False


def valid_media_path(path: object) -> bool:
    if not isinstance(path, str) or not path or '\\' in path or '\x00' in path:
        return False
    p = PurePosixPath(path)
    return (not p.is_absolute() and all(part not in ('.', '..') for part in path.split('/'))
            and p.suffix.lower() in {'.png', '.jpg', '.jpeg'} and path.startswith('assets/'))


def validate_manifest(manifest: object, ui_locales: set[str]) -> list[str]:
    issues: list[str] = []
    if not isinstance(manifest, dict):
        return ['Manifest must be an object']
    if manifest.get('schemaVersion') != 1:
        issues.append('Unsupported schemaVersion')
    if not isinstance(manifest.get('product'), str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]{2,79}', manifest['product']):
        issues.append('Invalid product identifier')
    if manifest.get('publicationStatus') != 'draft':
        issues.append('Manifest is draft-only: publicationStatus must be draft')
    entries = manifest.get('listings')
    if not isinstance(entries, list) or not entries:
        return issues + ['listings must be a nonempty array']
    seen: set[tuple[str, str]] = set()
    for index, entry in enumerate(entries):
        prefix = f'listings[{index}]'
        if not isinstance(entry, dict):
            issues.append(f'{prefix}: not an object')
            continue
        store = entry.get('store')
        ui = entry.get('uiLocale')
        target = entry.get('storeLocale')
        if not isinstance(store, str) or store not in STORES:
            issues.append(f'{prefix}: invalid store')
            continue
        for label, tag in [('uiLocale', ui), ('storeLocale', target)]:
            if not isinstance(tag, str) or not TAG.fullmatch(tag):
                issues.append(f'{prefix}: invalid {label}')
        if isinstance(ui, str) and ui not in ui_locales:
            issues.append(f'{prefix}: UI locale not in planned registry')
        if isinstance(target, str) and TAG.fullmatch(target):
            pair = (store, target)
            if pair in seen:
                issues.append(f'{prefix}: duplicate store/locale')
            seen.add(pair)
        if not isinstance(entry.get('status'), str) or entry['status'] not in APPROVED_STATUS:
            issues.append(f'{prefix}: unknown release status; no published state permitted')
        fields = entry.get('metadata')
        if not isinstance(fields, dict):
            issues.append(f'{prefix}: missing metadata object')
            continue
        allowed = GOOGLE_FIELDS if store == 'google-play' else APPLE_FIELDS
        required = allowed - ({'promotionalText'} if store == 'app-store' else set())
        if set(fields) - allowed:
            issues.append(f'{prefix}: unexpected metadata keys')
        if not required.issubset(fields):
            issues.append(f'{prefix}: missing required metadata fields')
        for key, value in fields.items():
            if key not in allowed:
                continue
            if not isinstance(value, str) or (key != 'promotionalText' and not value.strip()):
                issues.append(f'{prefix}: {key} must be nonempty text')
                continue
            if any((ord(c) < 32 and c not in '\n\t') or 0xD800 <= ord(c) <= 0xDFFF for c in value):
                issues.append(f'{prefix}: {key} contains control characters')
            if key in {'title', 'name', 'subtitle', 'shortDescription', 'keywords'} and ('\n' in value or '\r' in value):
                issues.append(f'{prefix}: {key} cannot contain line breaks')
            if key in {'fullDescription', 'description'} and re.search(r'<[^>]+>', value):
                issues.append(f'{prefix}: description cannot include HTML markup')
            limits = GOOGLE_LENGTHS if store == 'google-play' else APPLE_LENGTHS
            if key in limits and utf16_units(value) > limits[key]:
                issues.append(f'{prefix}: {key} exceeds {limits[key]} conservative UTF-16 units')
            if store == 'app-store' and key == 'name' and utf16_units(value) < 2:
                issues.append(f'{prefix}: Apple name must be at least two characters')
            if store == 'app-store' and key == 'keywords':
                if len(value.encode('utf-8', errors='surrogatepass')) > 100:
                    issues.append(f'{prefix}: Apple keywords exceed 100 UTF-8 bytes')
                words = [x.strip() for x in value.split(',')]
                if any(len(x) <= 2 for x in words) or len(set(w.casefold() for w in words)) != len(words):
                    issues.append(f'{prefix}: Apple keywords require distinct words longer than two characters')
        shots = entry.get('screenshots', [])
        if not isinstance(shots, list):
            issues.append(f'{prefix}: screenshots must be an array')
            continue
        media_paths: set[str] = set()
        for j, shot in enumerate(shots):
            if not isinstance(shot, dict) or not valid_media_path(shot.get('path')) or not isinstance(shot.get('sha256'), str) or not SHA256.fullmatch(shot['sha256']):
                issues.append(f'{prefix}: screenshots[{j}] has invalid asset path/hash')
                continue
            if shot['path'] in media_paths:
                issues.append(f'{prefix}: duplicate screenshot path')
            media_paths.add(shot['path'])
        if 'review' in entry and not isinstance(entry['review'], dict):
            issues.append(f'{prefix}: review must be an object')
    return issues


def release_preflight(manifest: object, ui_locales: set[str], assets_root: Path) -> list[str]:
    """Check author-supplied evidence. Passing is NOT permission to publish."""
    issues = validate_manifest(manifest, ui_locales)
    if issues or not isinstance(manifest, dict):
        return issues
    for index, entry in enumerate(manifest['listings']):
        prefix = f'listings[{index}]'
        if entry['status'] != 'reviewed':
            issues.append(f'{prefix}: must be independently reviewed before store submission')
        review = entry.get('review') or {}
        for field in APPROVAL_FIELDS:
            value = review.get(field)
            if not isinstance(value, str) or len(value.strip()) < 3:
                issues.append(f'{prefix}: missing {field} review evidence')
        locale_ref = review.get('storeLocaleSource')
        if not is_public_https(locale_ref):
            issues.append(f'{prefix}: store locale short code must be verified against official HTTPS documentation')
        screenshots = entry.get('screenshots', [])
        if len(screenshots) < 2:
            issues.append(f'{prefix}: at least two real localized screenshots required by Wexum policy')
        for shot in screenshots:
            if not valid_media_path(shot.get('path')):
                continue
            source = assets_root / shot['path']
            root = assets_root.resolve()
            real = source.resolve()
            if not real.is_relative_to(root) or not source.is_file():
                issues.append(f'{prefix}: missing or unsafe screenshot asset {shot["path"]}')
                continue
            relative_parts = PurePosixPath(shot['path']).parts
            probe = assets_root
            if any((probe := probe / part).is_symlink() for part in relative_parts):
                issues.append(f'{prefix}: symlink screenshot path forbidden {shot["path"]}')
                continue
            if source.stat().st_size > 8 * 1024 * 1024:
                issues.append(f'{prefix}: screenshot exceeds Wexum 8 MiB asset ceiling')
                continue
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest != shot['sha256']:
                issues.append(f'{prefix}: screenshot checksum mismatch {shot["path"]}')
        details = entry.get('storeContact', {})
        if not isinstance(details, dict):
            issues.append(f'{prefix}: storeContact required')
            continue
        if not is_public_https(details.get('privacyPolicyUrl')) or not is_public_https(details.get('supportUrl')):
            issues.append(f'{prefix}: HTTPS privacy and support URLs required')
        if entry['store'] == 'google-play':
            email = details.get('supportEmail')
            if not isinstance(email, str) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[A-Za-z]{2,}', email):
                issues.append(f'{prefix}: contact email required for Google Play')
    return issues


def load_known_ui_locales(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('locales'), list):
        raise ValueError('Missing Wexum locale registry')
    return {item['tag'] for item in data['locales'] if isinstance(item, dict) and isinstance(item.get('tag'), str)}


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate proposed Wexum store localization metadata')
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--registry', type=Path, default=Path(__file__).parent.parent / 'i18n/locales.json')
    parser.add_argument('--preflight', action='store_true', help='check human review and screenshot evidence; never publishes')
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        locales = load_known_ui_locales(args.registry)
        errors = (release_preflight(manifest, locales, args.manifest.parent) if args.preflight
                  else validate_manifest(manifest, locales))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f'Cannot validate manifest: {error}', file=sys.stderr)
        return 2
    if errors:
        for err in errors:
            print(f'ERROR: {err}', file=sys.stderr)
        return 1
    print(f'Validated {len(manifest["listings"])} draft storefront listings; no publishing performed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
