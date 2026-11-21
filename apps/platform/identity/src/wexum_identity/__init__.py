"""Isolated OAuth authorization transaction primitives; not an identity provider."""

from .callback import (
    AuthorizationCallback,
    AuthorizationResponseRejected,
    parse_authorization_callback,
)

from .exchange import UnverifiedCodeExchange, prepare_code_exchange

from .transport import decode_callback_pairs
from .webclient import ConfiguredWebOAuthClient

from .transactions import (
    AuthorizationCapacityExceeded,
    AuthorizationRejected,
    AuthorizationStart,
    AuthorizationTransactions,
    ExchangeContext,
)

__all__ = [
    "AuthorizationCallback",
    "AuthorizationResponseRejected",
    "parse_authorization_callback",
    "AuthorizationCapacityExceeded",
    "AuthorizationRejected",
    "AuthorizationStart",
    "AuthorizationTransactions",
    "ExchangeContext",
    "UnverifiedCodeExchange",
    "prepare_code_exchange",
    "decode_callback_pairs",
    "ConfiguredWebOAuthClient",
]
