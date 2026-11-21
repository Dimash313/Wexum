"""Offline release-evidence manifest linter. NOT a verifier of claims or safety.

This checks structure and declared evidence completeness only. External proof,
reviewer independence and actual security MUST be verified outside this tool.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REQUIRED_GATES = frozenset({
    "G-FOUNDATION", "G-IDENTITY", "G-TENANCY", "G-BILLING",
    "G-GRANTS", "G-NODES", "G-CLIENTS", "G-LEAK-TESTS",
    "G-PRIVACY", "G-RECOVERY", "G-CI", "G-INDEPENDENT",
    "G-COMPLIANCE",
})
GATE_STATES = frozenset({"blocked", "in_review", "attested"})
FINDING_STATES = frozenset({"open", "mitigated"})
SEVERITIES = frozenset({"critical", "high", "medium", "low"})
SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
GATE_RE = re.compile(r"G-[A-Z][A-Z0-9-]*\Z")
FINDING_RE = re.compile(r"SEC-[A-Z]+-[0-9]{3}\Z")


def _nonempty(value: Any) -> bool:
    return type(value) is str and bool(value.strip())


def _valid_evidence_url(value: Any) -> bool:
    """Require a real HTTPS authority; reject credentials and control characters."""
    if not _nonempty(value) or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and parsed.username is None and parsed.password is None
                and parsed.port != 0 and not value.startswith("https:///"))
    except ValueError:
        return False


def assess(manifest: Any) -> tuple[list[str], list[str]]:
    """Return (malformed metadata errors, unresolved readiness blockers).

    An empty blocker list only means the submitted *metadata* is complete.
    It does NOT prove tests ran, reviews occurred, or a VPN is safe.
    """
    errors: list[str] = []
    blockers: list[str] = []
    if not isinstance(manifest, dict):
        return ["root must be a JSON object"], []
    if type(manifest.get("schema_revision")) is not int or manifest["schema_revision"] != 1:
        errors.append("schema_revision must be integer 1")
    if manifest.get("scope") != "WexumVPN":
        errors.append("scope must be WexumVPN")
    sha = manifest.get("target_sha")
    if sha is not None and (type(sha) is not str or SHA_RE.fullmatch(sha) is None):
        errors.append("target_sha must be null or exactly 40 lower-case hex characters")
    gates = manifest.get("gates")
    if not isinstance(gates, list):
        return errors + ["gates must be an array"], blockers
    seen: set[str] = set()
    for index, gate in enumerate(gates):
        tag = f"gates[{index}]"
        if not isinstance(gate, dict):
            errors.append(f"{tag} must be an object")
            continue
        ident = gate.get("id")
        if not _nonempty(ident) or GATE_RE.fullmatch(ident) is None:
            errors.append(f"{tag}.id invalid")
            continue
        if ident in seen:
            errors.append(f"duplicate gate: {ident}")
        seen.add(ident)
        if not _nonempty(gate.get("owner")) or not _nonempty(gate.get("criterion")):
            errors.append(f"{ident}: owner and criterion are mandatory")
        state = gate.get("state")
        if type(state) is not str or state not in GATE_STATES:
            errors.append(f"{ident}: invalid state")
            continue
        evidence = gate.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{ident}: evidence must be an array")
            continue
        if state != "attested":
            blockers.append(f"{ident}: {state}")
            if evidence:
                errors.append(f"{ident}: pending/blocked gate may not claim accepted evidence")
            continue
        if sha is None:
            errors.append(f"{ident}: attested gate requires a target_sha")
        seen_kinds: set[str] = set()
        actors: dict[str, str] = {}
        for j, record in enumerate(evidence):
            if not isinstance(record, dict):
                errors.append(f"{ident}: evidence[{j}] must be object")
                continue
            kind = record.get("kind")
            if kind not in ("verification", "independent_review") or kind in seen_kinds:
                errors.append(f"{ident}: evidence kind must be unique verification/independent_review")
                continue
            seen_kinds.add(kind)
            actor = record.get("actor")
            uri = record.get("url")
            if not _nonempty(actor) or not _valid_evidence_url(uri):
                errors.append(f"{ident}: evidence requires actor and HTTPS URL")
            else:
                actors[kind] = actor
            if type(record.get("commit_sha")) is not str or record["commit_sha"] != sha:
                errors.append(f"{ident}: evidence commit does not match target_sha")
        if seen_kinds != {"verification", "independent_review"}:
            errors.append(f"{ident}: require verification AND independent_review evidence")
        if len(actors) == 2 and actors["verification"] == actors["independent_review"]:
            errors.append(f"{ident}: evidence submitter and reviewer must differ")
    missing = REQUIRED_GATES - seen
    if missing:
        errors.append("missing mandatory gates: " + ", ".join(sorted(missing)))
    findings = manifest.get("findings")
    if not isinstance(findings, list):
        return errors + ["findings must be an array"], blockers
    finding_ids: set[str] = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            errors.append(f"findings[{index}] must be object")
            continue
        ident = finding.get("id")
        if not _nonempty(ident) or FINDING_RE.fullmatch(ident) is None:
            errors.append(f"findings[{index}].id invalid")
            continue
        if ident in finding_ids:
            errors.append(f"duplicate finding: {ident}")
        finding_ids.add(ident)
        severity = finding.get("severity")
        state = finding.get("state")
        if type(severity) is not str or severity not in SEVERITIES or type(state) is not str or state not in FINDING_STATES:
            errors.append(f"{ident}: invalid severity/state")
        if not all(_nonempty(finding.get(key)) for key in ("owner", "source", "description")):
            errors.append(f"{ident}: owner, source and description are mandatory")
        if state == "open" and severity in {"critical", "high"}:
            blockers.append(f"{ident}: unresolved {severity} finding")
    return errors, blockers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path,
                        default=Path(__file__).with_name("release_gates.json"))
    parser.add_argument("--require-attested", action="store_true",
                        help="Fail if any recorded release gate/finding remains open")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"INVALID MANIFEST: {type(error).__name__}")
        return 2
    errors, blockers = assess(manifest)
    if errors:
        for error in errors:
            print(f"INVALID MANIFEST: {error}")
        return 2
    print(f"SCHEMA OK; {len(blockers)} unresolved metadata blockers; "
          "this tool does NOT verify security evidence or grant release.")
    if args.require_attested:
        for item in blockers:
            print(f"BLOCKED: {item}")
        # No offline self-attestation can verify real artifacts, reviewer
        # independence or production safety. Never return a release-green
        # exit code from this metadata-only tool, even for a fully populated
        # manifest. External verified evidence needs a separate approval gate.
        if not blockers:
            print("BLOCKED: independent, externally verified release evidence is required")
        return 1
    if not blockers:
        print("METADATA COMPLETE ONLY — independent verification still mandatory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
