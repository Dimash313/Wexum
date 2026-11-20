"""Deny-by-default resource authorization contract.

This pure function is not authentication or a complete policy engine. A service must
authenticate the principal and load trusted tenant membership before calling it.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


class Action(StrEnum):
    READ = "read"
    WRITE = "write"
    MANAGE = "manage"


class ResourceKind(StrEnum):
    PERSONAL = "personal"
    ORGANIZATION = "organization"


_ROLE_ACTIONS: Mapping[str, frozenset[Action]] = {
    "viewer": frozenset({Action.READ}),
    "editor": frozenset({Action.READ, Action.WRITE}),
    "admin": frozenset(Action),
}


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: str
    organization_roles: Mapping[str, frozenset[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        snapshot = {tenant: frozenset(roles) for tenant, roles in self.organization_roles.items()}
        object.__setattr__(self, "organization_roles", MappingProxyType(snapshot))


@dataclass(frozen=True, slots=True)
class Resource:
    kind: ResourceKind
    tenant_id: str


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    reason: str


def authorize(principal: Principal, resource: Resource, action: Action) -> Decision:
    """Authorize a trusted principal for one tenant-scoped resource.

    Unknown kinds/actions/roles and missing IDs are denied; no implicit superuser.
    """
    if not principal.user_id or not resource.tenant_id:
        return Decision(False, "invalid_identity")
    if not isinstance(action, Action) or not isinstance(resource.kind, ResourceKind):
        return Decision(False, "invalid_request")
    if resource.kind is ResourceKind.PERSONAL:
        permitted = principal.user_id == resource.tenant_id
        return Decision(permitted, "owner" if permitted else "cross_tenant")
    roles = principal.organization_roles.get(resource.tenant_id, frozenset())
    permitted = any(action in _ROLE_ACTIONS.get(role, frozenset()) for role in roles)
    return Decision(permitted, "role_grant" if permitted else "no_grant")

