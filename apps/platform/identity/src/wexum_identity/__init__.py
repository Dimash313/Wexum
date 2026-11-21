"""Isolated OAuth authorization transaction primitives; not an identity provider."""

from .callback import (
    AuthorizationCallback,
    AuthorizationResponseRejected,
    parse_authorization_callback,
)

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
]
