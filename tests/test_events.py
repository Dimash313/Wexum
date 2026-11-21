import unittest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from wexum_core.events import EventEnvelope


class EventEnvelopeTests(unittest.TestCase):
    def test_create_is_unique_and_timezone_aware(self):
        a = EventEnvelope.create(event_type="cloud.file.created", tenant_id="tenant-a")
        b = EventEnvelope.create(event_type="cloud.file.created", tenant_id="tenant-a")
        self.assertNotEqual(a.event_id, b.event_id)
        self.assertIsNotNone(a.occurred_at.tzinfo)
        self.assertEqual(a.schema_revision, 1)

    def test_rejects_invalid_metadata(self):
        for event_type, tenant_id, revision in [("", "org", 1), ("event", "", 1), ("event", "org", 0)]:
            with self.subTest(event_type=event_type, tenant_id=tenant_id, revision=revision):
                with self.assertRaises(ValueError):
                    EventEnvelope(uuid4(), event_type, revision, tenant_id, datetime.now(timezone.utc))

    def test_rejects_malformed_event_contract(self):
        now = datetime.now(timezone.utc)
        invalid = [
            ("not-a-uuid", "event", 1, "org", now),
            (UUID(int=0), "event", 1, "org", now),
            (uuid4(), None, 1, "org", now),
            (uuid4(), "event", 1, None, now),
            (uuid4(), "event", True, "org", now),
            (uuid4(), "event", 1.5, "org", now),
            (uuid4(), "event", 1, "org", "not-a-date"),
        ]
        for values in invalid:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    EventEnvelope(*values)

    def test_rejects_naive_timestamps(self):
        with self.assertRaises(ValueError):
            EventEnvelope(uuid4(), "event", 1, "org", datetime.now())


if __name__ == "__main__":
    unittest.main()

