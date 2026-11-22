"""Strict, framework-neutral authorization-code callback parameter boundary.

Input is a sequence of already URL/form-decoded (name, value) pairs.  Using a
mapping is deliberately prohibited: it can silently hide duplicate parameters.
This parser is not a token verifier, an HTTP adapter or an authentication step.
"""

from dataclasses import dataclass, field
from urllib.parse import urlsplit


class AuthorizationResponseRejected(Exception):
    """Untrusted authorization response must not continue to token exchange."""


@dataclass(frozen=True, slots=True)
class AuthorizationCallback:
    """An untrusted code response requiring session-bound state consumption."""

    state: str = field(repr=False)
    code: str = field(repr=False)
    response_issuer: str


def parse_authorization_callback(pairs: list[tuple[str, str]] | tuple[tuple[str, str], ...]) -> AuthorizationCallback:
    """Validate a decoded OAuth code response without treating it as a login.

    The HTTP layer must collect query OR form-body pairs preserving duplicates,
    reject mixed transport/duplicate sources, and cap request byte size itself.
    Callers must then bind the returned state and issuer to a trusted browser
    session via AuthorizationTransactions.consume BEFORE exchanging the code.
    """
    reject = "invalid authorization response"
    if type(pairs) not in (list, tuple) or not 1 <= len(pairs) <= 32:
        raise AuthorizationResponseRejected(reject)
    fields: dict[str, str] = {}
    total_bytes = 0
    for pair in pairs:
        if type(pair) not in (list, tuple) or len(pair) != 2:
            raise AuthorizationResponseRejected(reject)
        key, value = pair
        if (
            not isinstance(key, str)
            or not isinstance(value, str)
            or not 1 <= len(key) <= 64
            or len(value) > 4096
            or not key.isascii()
            or not key.isprintable()
            or not value.isprintable()
            or key in fields
        ):
            raise AuthorizationResponseRejected(reject)
        total_bytes += len(key.encode("utf-8")) + len(value.encode("utf-8"))
        if total_bytes > 8192:
            raise AuthorizationResponseRejected(reject)
        fields[key] = value

    # OAuth request or response parameters must never be repeated; an error
    # cannot be interpreted as a successful authorization code response.
    if "error" in fields or any(not fields.get(k) for k in ("code", "state", "iss")):
        raise AuthorizationResponseRejected(reject)
    if any(len(fields[k]) > 2048 or fields[k] != fields[k].strip() for k in ("state", "iss")):
        raise AuthorizationResponseRejected(reject)

    issuer = fields["iss"]
    try:
        uri = urlsplit(issuer)
        if (
            uri.scheme != "https"
            or not uri.hostname
            or uri.username is not None
            or uri.password is not None
            or "?" in issuer
            or "#" in issuer
            or uri.port == 0
        ):
            raise AuthorizationResponseRejected(reject)
    except ValueError as exc:
        raise AuthorizationResponseRejected(reject) from exc

    return AuthorizationCallback(
        state=fields["state"], code=fields["code"], response_issuer=issuer
    )
