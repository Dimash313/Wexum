"""Pinned browser OAuth client configuration, without login or HTTP serving.

Objects MUST be constructed from trusted deployment configuration, never
request fields. Syntactic validation does not authenticate an OIDC issuer.
Only HTTPS browser redirects are supported; native loopback/custom schemes
require a separate reviewed contract.
"""

from dataclasses import dataclass
from urllib.parse import urlsplit

from .exchange import UnverifiedCodeExchange, prepare_code_exchange
from .transactions import AuthorizationStart, AuthorizationTransactions
from .transport import decode_callback_pairs


def _https_url(value: str, *, label: str) -> None:
    if (
        type(value) is not str
        or not value
        or len(value) > 2048
        or any(not ch.isprintable() or ch.isspace() for ch in value)
        or "\\" in value
        or "?" in value
        or "#" in value
    ):
        raise ValueError(f"invalid {label}")
    try:
        url = urlsplit(value)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username is not None
            or url.password is not None
            or "@" in url.netloc
            or "%" in url.netloc
            or url.port == 0
            or url.netloc.endswith(":")
        ):
            raise ValueError(f"invalid {label}")
    except ValueError:
        raise ValueError(f"invalid {label}") from None


@dataclass(frozen=True, slots=True)
class ConfiguredWebOAuthClient:
    """Immutable, HTTPS-only OAuth client settings selected by the server.

    No provider discovery, registered redirect verification or cryptographic
    verification is performed. Holding this object is not an authorization.
    """

    issuer: str
    client_id: str
    redirect_uri: str
    response_mode: str = "query"

    def __post_init__(self) -> None:
        _https_url(self.issuer, label="issuer")
        _https_url(self.redirect_uri, label="redirect_uri")
        if (
            type(self.client_id) is not str
            or not self.client_id
            or len(self.client_id) > 2048
            or self.client_id != self.client_id.strip()
            or not self.client_id.isprintable()
        ):
            raise ValueError("invalid client_id")
        if type(self.response_mode) is not str or self.response_mode not in ("query", "form_post"):
            raise ValueError("invalid response_mode")

    def begin(self, transactions: AuthorizationTransactions, *, browser_session: str) -> AuthorizationStart:
        """Start a pending attempt, always using pinned server configuration."""
        return transactions.begin(
            browser_session=browser_session,
            issuer=self.issuer,
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
        )

    def prepare_callback(
        self,
        transactions: AuthorizationTransactions,
        *,
        browser_session: str,
        method: str,
        query_string: bytes = b"",
        body: bytes = b"",
        content_type: str | None = None,
    ) -> UnverifiedCodeExchange:
        """Decode exactly the configured mode, then consume a matching state.

        The HTTP caller must supply raw undecoded bytes and separately enforce
        request size limits and a valid authenticated browser-session binding.
        The output is NOT a verified user, token, or server-side login.
        """
        pairs = decode_callback_pairs(
            method=method,
            response_mode=self.response_mode,
            query_string=query_string,
            body=body,
            content_type=content_type,
        )
        return prepare_code_exchange(
            transactions,
            decoded_pairs=pairs,
            browser_session=browser_session,
            issuer=self.issuer,
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
        )
