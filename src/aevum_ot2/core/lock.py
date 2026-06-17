from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT
from aevum_ot2.core.models import BridgeLock

DEFAULT_STATE_DB = ROOT / "data" / "measurements" / "ot2_bridge_state.sqlite3"
TERMINAL_LOCK_STATES = {"closed", "failed", "released"}


@dataclass(frozen=True)
class LockAcquireResult:
    acquired: bool
    lock: BridgeLock


def initialize_state_db(path: str | Path = DEFAULT_STATE_DB) -> Path:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bridge_locks (
                robot_url TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                lease_started_at TEXT NOT NULL,
                lease_expires_at TEXT NOT NULL,
                active_run_id TEXT,
                last_command_id TEXT,
                state TEXT NOT NULL,
                lease_kind TEXT NOT NULL DEFAULT 'pipetting'
            )
            """
        )
        _migrate_lease_kind_column(connection)
    return db_path


def _migrate_lease_kind_column(connection: sqlite3.Connection) -> None:
    """Add ``lease_kind`` to a pre-IN-C4 ``bridge_locks`` table (defaults to pipetting).

    A DB created before the observer lease existed has no ``lease_kind`` column;
    ``CREATE TABLE IF NOT EXISTS`` is a no-op there, so migrate explicitly. Existing rows
    backfill to ``pipetting`` (they were all OT-2 leases), which is the fail-safe default:
    an unlabeled legacy lock is treated as the pipetting lease it actually was.
    """
    columns = {row[1] for row in connection.execute("PRAGMA table_info(bridge_locks)")}
    if "lease_kind" not in columns:
        connection.execute(
            "ALTER TABLE bridge_locks ADD COLUMN lease_kind TEXT NOT NULL DEFAULT 'pipetting'"
        )


def lease_is_held(lock: BridgeLock, now: datetime) -> bool:
    """A lock holds its lease while non-terminal AND unexpired (fail-closed).

    The single source of truth for 'this lock currently has motion authority' across the
    bridge: it gates whether a lock blocks a new session and whether an observer frame may
    be minted, so both paths mean exactly the same thing by 'valid lease'.
    """
    return lock.state not in TERMINAL_LOCK_STATES and lock.lease_expires_at > now


def read_lock(robot_url: str, path: str | Path = DEFAULT_STATE_DB) -> BridgeLock | None:
    db_path = initialize_state_db(path)
    with sqlite3.connect(db_path) as connection:
        return read_lock_in_transaction(connection, robot_url)


def read_lock_in_transaction(
    connection: sqlite3.Connection,
    robot_url: str,
) -> BridgeLock | None:
    row = connection.execute(
        """
        SELECT robot_url, session_id, owner_id, lease_started_at, lease_expires_at,
               active_run_id, last_command_id, state, lease_kind
        FROM bridge_locks
        WHERE robot_url = ?
        """,
        (robot_url,),
    ).fetchone()
    if row is None:
        return None
    return _lock_from_row(row)


def write_lock(lock: BridgeLock, path: str | Path = DEFAULT_STATE_DB) -> None:
    db_path = initialize_state_db(path)
    with sqlite3.connect(db_path) as connection:
        write_lock_in_transaction(connection, lock)


def write_lock_in_transaction(
    connection: sqlite3.Connection,
    lock: BridgeLock,
) -> None:
    _write_lock_row(connection, lock)


def acquire_lock(
    lock: BridgeLock,
    path: str | Path = DEFAULT_STATE_DB,
) -> LockAcquireResult:
    db_path = initialize_state_db(path)
    with sqlite3.connect(db_path, isolation_level=None) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            row = connection.execute(
                """
                SELECT robot_url, session_id, owner_id, lease_started_at,
                       lease_expires_at, active_run_id, last_command_id, state, lease_kind
                FROM bridge_locks
                WHERE robot_url = ?
                """,
                (lock.robot_url,),
            ).fetchone()
            if row is not None:
                existing = _lock_from_row(row)
                if existing.state not in TERMINAL_LOCK_STATES:
                    connection.rollback()
                    return LockAcquireResult(acquired=False, lock=existing)
            _write_lock_row(connection, lock)
            connection.commit()
            return LockAcquireResult(acquired=True, lock=lock)
        except Exception:
            connection.rollback()
            raise


def _write_lock_row(connection: sqlite3.Connection, lock: BridgeLock) -> None:
    connection.execute(
        """
        INSERT INTO bridge_locks (
            robot_url, session_id, owner_id, lease_started_at, lease_expires_at,
            active_run_id, last_command_id, state, lease_kind
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(robot_url) DO UPDATE SET
            session_id = excluded.session_id,
            owner_id = excluded.owner_id,
            lease_started_at = excluded.lease_started_at,
            lease_expires_at = excluded.lease_expires_at,
            active_run_id = excluded.active_run_id,
            last_command_id = excluded.last_command_id,
            state = excluded.state,
            lease_kind = excluded.lease_kind
        """,
        (
            lock.robot_url,
            lock.session_id,
            lock.owner_id,
            lock.lease_started_at.isoformat(),
            lock.lease_expires_at.isoformat(),
            lock.active_run_id,
            lock.last_command_id,
            lock.state,
            str(lock.lease_kind),
        ),
    )


def _lock_from_row(row: tuple[object, ...]) -> BridgeLock:
    return BridgeLock(
        robot_url=str(row[0]),
        session_id=str(row[1]),
        owner_id=str(row[2]),
        lease_started_at=datetime.fromisoformat(str(row[3])),
        lease_expires_at=datetime.fromisoformat(str(row[4])),
        active_run_id=row[5] if isinstance(row[5], str) else None,
        last_command_id=row[6] if isinstance(row[6], str) else None,
        state=str(row[7]),
        lease_kind=str(row[8]) if len(row) > 8 and row[8] is not None else "pipetting",
    )
