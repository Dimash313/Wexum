"""Strict, framework-independent OAuth callback form/query decoding.

This is not an HTTP server. The HTTP adapter MUST pass raw request-target
query bytes and raw body bytes separately, before any framework normalization.
It MUST also enforce network/header/body limits before reading these bytes.
"""

import re
from urllib.parse import unquote_to_bytes

from .callback import AuthorizationResponseRejected


_BAD_PERCENT = re.compile(rb"%(?![0-9A-Fa-f]{2})")
_MAX_RAW_BYTES = 8192


def decode_callback_pairs(
    *,
    method: str,
    response_mode: str,
    query_string: bytes = b"",
    body: bytes = b"",
    content_type: str | None = None,
) -> tuple[tuple[str, str], ...]:
    """Decode exactly one trusted response mode, preserving duplicate fields.

    `response_mode` MUST be chosen from trusted registered client settings,
    NEVER inferred from an incoming request. Only `query` (GET) or `form_post`
    (POST application/x-www-form-urlencoded) are accepted; the form-post
    redirect URI must have no static query component. This policy deliberately
    does not support implicit, hybrid, JWT, JARM, or fragment responses.

    The caller MUST subsequently use `parse_authorization_callback()` and
    `AuthorizationTransactions.consume()` (or `prepare_code_exchange()`).
    Raw byte/encoding ambiguity is rejected, and errors reveal no callback
    secrets. No authentication or exchange takes place here.
    """
    bad = "invalid authorization response"
    if type(query_string) is not bytes or type(body) is not bytes:
        raise AuthorizationResponseRejected(bad)
    if len(query_string) > _MAX_RAW_BYTES or len(body) > _MAX_RAW_BYTES:
        raise AuthorizationResponseRejected(bad)
    if method == "GET" and response_mode == "query":
        if body or content_type not in (None, ""):
            raise AuthorizationResponseRejected(bad)
        raw = query_string
    elif method == "POST" and response_mode == "form_post":
        if query_string or type(content_type) is not str:
            raise AuthorizationResponseRejected(bad)
        mime = content_type.strip().lower()
        if mime not in ("application/x-www-form-urlencoded", "application/x-www-form-urlencoded; charset=utf-8"):
            raise AuthorizationResponseRejected(bad)
        raw = body
    else:
        raise AuthorizationResponseRejected(bad)

    if not raw or len(raw) > _MAX_RAW_BYTES:
        raise AuthorizationResponseRejected(bad)
    # Transport components must be ASCII on the wire; Unicode values must be
    # percent-encoded as UTF-8, eliminating intermediary decoding ambiguity.
    if any(byte < 0x20 or byte > 0x7E or byte == ord("#") for byte in raw):
        raise AuthorizationResponseRejected(bad)
    components = raw.split(b"&")
    if len(components) > 32:
        raise AuthorizationResponseRejected(bad)

    result: list[tuple[str, str]] = []
    for component in components:
        if b"=" not in component:
            raise AuthorizationResponseRejected(bad)
        name, value = component.split(b"=", 1)
        if not name or _BAD_PERCENT.search(name) or _BAD_PERCENT.search(value):
            raise AuthorizationResponseRejected(bad)
        try:
            key = unquote_to_bytes(name.replace(b"+", b" ")).decode("utf-8", errors="strict")
            decoded = unquote_to_bytes(value.replace(b"+", b" ")).decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise AuthorizationResponseRejected(bad) from exc
        result.append((key, decoded))
    return tuple(result)
