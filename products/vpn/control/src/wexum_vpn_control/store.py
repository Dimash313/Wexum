"""Transactional, tenant-and-subject-scoped SQLite state; no network IO."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Device:
    device_id: str
    tenant_id: str
    subject_id: str
    platform: str
    registered_at: str
    expires_at: str
    revoked_at: str | None


def utc_stamp(moment: datetime) -> str:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError('timezone-aware datetime required')
    return moment.astimezone(timezone.utc).isoformat(timespec='microseconds')


def _record(row: tuple) -> Device:
    return Device(*row)


class StoreBusy(Exception):
    pass


class StoreConflict(Exception):
    pass


class StoreLimit(Exception):
    pass


class SQLiteDeviceStore:
    """Single-file transaction-protected prototype. Not a multi-region database."""

    def __init__(self, path: str | Path, *, busy_timeout_seconds: float = 2.0):
        self.path = Path(path)
        if not (0.1 <= busy_timeout_seconds <= 30.0):
            raise ValueError('invalid database timeout')
        self.busy_timeout_seconds = busy_timeout_seconds
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        # SQLite files must be under a trusted server-owned directory. Do not
        # construct paths from tenant/user input. Symlink defense belongs in deployment.
        connection = sqlite3.connect(self.path, timeout=self.busy_timeout_seconds,
                                     isolation_level=None)
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute(f'PRAGMA busy_timeout={int(self.busy_timeout_seconds * 1000)}')
        return connection

    def _initialize(self) -> None:
        connection = self._connect()
        try:
            connection.execute('PRAGMA journal_mode=WAL')
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT
                );
                CREATE INDEX IF NOT EXISTS device_owner_lookup
                    ON devices (tenant_id, subject_id, revoked_at, expires_at);
                CREATE TABLE IF NOT EXISTS enrollment_requests (
                    tenant_id TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    device_id TEXT NOT NULL REFERENCES devices(device_id),
                    PRIMARY KEY (tenant_id, subject_id, request_hash)
                );
            ''')
        finally:
            connection.close()

    def enroll(self, *, tenant_id: str, subject_id: str, platform: str,
               request_key: str, now: datetime, expires_at: datetime,
               max_devices: int) -> Device:
        now_text, expiry_text = utc_stamp(now), utc_stamp(expires_at)
        if expiry_text <= now_text or max_devices < 1:
            raise ValueError('invalid enrollment expiry/limit')
        # Hash idempotency keys rather than retaining raw client tokens.
        request_hash = hashlib.sha256(request_key.encode('utf-8')).hexdigest()
        connection = self._connect()
        try:
            connection.execute('BEGIN IMMEDIATE')
            prior = connection.execute('''
                SELECT platform, device_id FROM enrollment_requests
                WHERE tenant_id=? AND subject_id=? AND request_hash=?
            ''', (tenant_id, subject_id, request_hash)).fetchone()
            if prior is not None:
                if prior[0] != platform:
                    raise StoreConflict('idempotency key used for different request')
                row = connection.execute('''
                    SELECT device_id, tenant_id, subject_id, platform,
                           registered_at, expires_at, revoked_at FROM devices
                    WHERE device_id=? AND tenant_id=? AND subject_id=?
                ''', (prior[1], tenant_id, subject_id)).fetchone()
                if row is None:
                    raise StoreConflict('idempotency record without device')
                connection.execute('COMMIT')
                return _record(row)
            count = connection.execute('''
                SELECT COUNT(*) FROM devices
                WHERE tenant_id=? AND subject_id=?
                  AND revoked_at IS NULL AND expires_at>?
            ''', (tenant_id, subject_id, now_text)).fetchone()[0]
            if count >= max_devices:
                raise StoreLimit('device limit reached')
            device = Device(str(uuid.uuid4()), tenant_id, subject_id, platform,
                            now_text, expiry_text, None)
            connection.execute('''
                INSERT INTO devices(device_id, tenant_id, subject_id, platform,
                                    registered_at, expires_at, revoked_at)
                VALUES (?, ?, ?, ?, ?, ?, NULL)
            ''', (device.device_id, tenant_id, subject_id, platform,
                  now_text, expiry_text))
            connection.execute('''
                INSERT INTO enrollment_requests
                  (tenant_id, subject_id, request_hash, platform, device_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (tenant_id, subject_id, request_hash, platform, device.device_id))
            connection.execute('COMMIT')
            return device
        except sqlite3.Error as error:
            if connection.in_transaction:
                connection.execute('ROLLBACK')
            raise StoreBusy('device store unavailable') from error
        except BaseException:
            if connection.in_transaction:
                connection.execute('ROLLBACK')
            raise
        finally:
            connection.close()

    def list_for_owner(self, *, tenant_id: str, subject_id: str) -> list[Device]:
        connection = self._connect()
        try:
            rows = connection.execute('''
                SELECT device_id, tenant_id, subject_id, platform,
                       registered_at, expires_at, revoked_at FROM devices
                WHERE tenant_id=? AND subject_id=?
                ORDER BY registered_at ASC, device_id ASC LIMIT 200
            ''', (tenant_id, subject_id)).fetchall()
            return [_record(row) for row in rows]
        except sqlite3.Error as error:
            raise StoreBusy('device store unavailable') from error
        finally:
            connection.close()

    def revoke(self, *, tenant_id: str, subject_id: str,
               device_id: str, now: datetime) -> Device | None:
        connection = self._connect()
        try:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('''
                SELECT device_id, tenant_id, subject_id, platform,
                       registered_at, expires_at, revoked_at FROM devices
                WHERE device_id=? AND tenant_id=? AND subject_id=?
            ''', (device_id, tenant_id, subject_id)).fetchone()
            if row is None:
                connection.execute('COMMIT')
                return None
            if row[6] is None:
                connection.execute('''
                    UPDATE devices SET revoked_at=?
                    WHERE device_id=? AND tenant_id=? AND subject_id=? AND revoked_at IS NULL
                ''', (utc_stamp(now), device_id, tenant_id, subject_id))
                row = connection.execute('''
                    SELECT device_id, tenant_id, subject_id, platform,
                           registered_at, expires_at, revoked_at FROM devices
                    WHERE device_id=? AND tenant_id=? AND subject_id=?
                ''', (device_id, tenant_id, subject_id)).fetchone()
            connection.execute('COMMIT')
            return _record(row)
        except sqlite3.Error as error:
            if connection.in_transaction:
                connection.execute('ROLLBACK')
            raise StoreBusy('device store unavailable') from error
        except BaseException:
            if connection.in_transaction:
                connection.execute('ROLLBACK')
            raise
        finally:
            connection.close()
