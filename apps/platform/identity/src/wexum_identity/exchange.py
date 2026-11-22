"""Provider-neutral pre-exchange handoff, not login or token validation.

This composes the strict untrusted callback parser and a process-local,
session-bound, single-use authorization transaction. It performs no network
request, identity assertion, scope check, or user-session creation.
"""

from dataclasses import dataclass, field

from .callback import parse_authorization_callback
from .transactions import AuthorizationTransactions


@dataclass(frozen=True, slots=True)
class UnverifiedCodeExchange:
    """Sensitive inputs for a future trusted token adapter; never a principal.

    The outer adapter MUST pin its discovery and token endpoint to `issuer`,
    then verify signed ID tokens, audience, time, nonce, and access rights.
    No field of this object proves an authenticated or authorized user.
    """

    authorization_code: str = field(repr=False)
    code_verifier: str = field(repr=False)
    expected_nonce: str = field(repr=False)
    issuer: str
    client_id: str
    redirect_uri: str


def prepare_code_exchange(
    transactions: AuthorizationTransactions,
    *,
    decoded_pairs: list[tuple[str, str]] | tuple[tuple[str, str], ...],
    browser_session: str,
    issuer: str,
    client_id: str,
    redirect_uri: str,
) -> UnverifiedCodeExchange:
    """Validate callback then atomically consume its server-bound state once.

    `decoded_pairs` MUST come from exactly one HTTP response transport, with
    duplicate keys preserved and a bounded raw request before decoding. The
    browser session and provider/client/redirect configuration MUST come from
    trusted server context, not from callback fields or client-controlled
    request parameters. The caller must NOT treat a returned object as login.

    Malformed callback input never consumes a pending transaction. After a
    successful consume, even a later failed token exchange requires a fresh
    authorization attempt; retrying this callback will be rejected.
    """
    callback = parse_authorization_callback(decoded_pairs)
    context = transactions.consume(
        state=callback.state,
        response_issuer=callback.response_issuer,
        browser_session=browser_session,
        issuer=issuer,
        client_id=client_id,
        redirect_uri=redirect_uri,
    )
    return UnverifiedCodeExchange(
        authorization_code=callback.code,
        code_verifier=context.code_verifier,
        expected_nonce=context.expected_nonce,
        issuer=issuer,
        client_id=client_id,
        redirect_uri=redirect_uri,
    )
