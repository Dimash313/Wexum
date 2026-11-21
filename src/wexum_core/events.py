"""Minimal immutable event envelope; transports must implement durable delivery."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event_id: UUID
    event_type: str
    schema_revision: int
    tenant_id: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, UUID) or self.event_id.int == 0:
            raise ValueError("event_id must be a nonzero UUID")
        if not isinstance(self.event_type, str) or not self.event_type.strip():
            raise ValueError("event_type is required")
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if type(self.schema_revision) is not int or self.schema_revision < 1:
            raise ValueError("schema_revision must be a positive integer")
        if not isinstance(self.occurred_at, datetime):
            raise ValueError("occurred_at must be a datetime")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")

    @classmethod
    def create(cls, *, event_type: str, tenant_id: str, schema_revision: int = 1) -> "EventEnvelope":
        return cls(
            event_id=uuid4(),
            event_type=event_type,
            schema_revision=schema_revision,
            tenant_id=tenant_id,
            occurred_at=datetime.now(timezone.utc),
        )

