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
        if not self.event_type.strip() or not self.tenant_id.strip():
            raise ValueError("event_type and tenant_id are required")
        if self.schema_revision < 1:
            raise ValueError("schema_revision must be positive")
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

