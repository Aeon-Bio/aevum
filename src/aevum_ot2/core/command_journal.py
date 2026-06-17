from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from aevum_ot2.core.evidence_primitives import _stable_json_sha256
from aevum_ot2.core.lock import DEFAULT_STATE_DB
from aevum_ot2.core.models import BridgeSession, BridgeSessionState, EndpointResult
from aevum_ot2.core.plans import PlanStep
from aevum_ot2.core.schema import loads_json_object, parse_versioned_json_model

CommandJournalState = Literal[
    "prepared",
    "dispatching",
    "posted",
    "accepted",
    "completed",
    "failed",
    "ambiguous",
    "recovery_required",
]

COMMAND_TERMINAL_STATES = {"completed", "failed", "recovery_required"}
COMMAND_AMBIGUOUS_STATES = {"ambiguous", "recovery_required"}
COMMAND_SUCCESS_STATUSES = {"succeeded", "completed"}
COMMAND_FAILURE_STATUSES = {"failed", "stopped", "canceled", "cancelled"}


class CommandJournalEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    journal_id: str
    session_id: str
    owner_id: str
    robot_url: str
    run_id: str
    step_id: str
    operation: str
    command_key: str
    command_type: str
    command_body_sha256: str
    command_params_sha256: str
    state: CommandJournalState = "prepared"
    prepared_at: datetime = Field(default_factory=datetime.now)
    posted_at: datetime | None = None
    reconciled_at: datetime | None = None
    command_id: str | None = None
    command_index: int | None = None
    command_status: str | None = None
    response_status_code: int | None = None
    blockers: list[str] = Field(default_factory=list)


class CommandJournalWriteResult(BaseModel):
    persisted: bool
    entry: CommandJournalEntry | None = None
    blocker: str = ""


class CommandDispatchResult(BaseModel):
    entry: CommandJournalEntry
    journal_persisted: bool
    posted: bool = False
    post_result: EndpointResult | None = None
    reconciliation: CommandReconciliationResult | None = None
    blockers: list[str] = Field(default_factory=list)


class CommandReconciliationResult(BaseModel):
    entry: CommandJournalEntry | None = None
    state: CommandJournalState
    matched_command_id: str | None = None
    matched_command_index: int | None = None
    command_history_total_length: int | None = None
    matched_command_is_latest: bool = False
    matched_status: str | None = None
    blockers: list[str] = Field(default_factory=list)
    recovery_required: bool = False
    non_idempotent_duplicate_key: bool = False


class CommandTransport(Protocol):
    def post_json(
        self,
        path: str,
        body: dict[str, Any] | list[Any] | None = None,
    ) -> EndpointResult: ...

    def get_json(self, path: str) -> EndpointResult: ...


def initialize_command_journal_db(path: str | Path = DEFAULT_STATE_DB) -> Path:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as connection:
        ensure_command_journal_table(connection)
    return db_path


def ensure_command_journal_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS command_journal (
            journal_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            robot_url TEXT NOT NULL,
            run_id TEXT NOT NULL,
            command_key TEXT NOT NULL,
            command_type TEXT NOT NULL,
            state TEXT NOT NULL,
            prepared_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_command_journal_session
        ON command_journal(session_id, prepared_at)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_command_journal_run_key
        ON command_journal(run_id, command_key)
        """
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_command_journal_run_key_unique
        ON command_journal(run_id, command_key)
        """
    )


def new_command_journal_entry(
    *,
    session: BridgeSession,
    step: PlanStep,
    run_id: str,
    command_body: dict[str, Any],
    journal_id: str | None = None,
    prepared_at: datetime | None = None,
) -> CommandJournalEntry:
    command_data = _command_data(command_body)
    command_key = _required_command_string(command_data, "key")
    command_type = _required_command_string(command_data, "commandType")
    command_params = command_data.get("params")
    if not isinstance(command_params, dict):
        command_params = {}
    return CommandJournalEntry(
        journal_id=journal_id or f"cmd-{uuid4().hex}",
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=run_id,
        step_id=step.step_id,
        operation=step.operation,
        command_key=command_key,
        command_type=command_type,
        command_body_sha256=_stable_json_sha256(command_body),
        command_params_sha256=_stable_command_params_sha256(
            command_type,
            command_params,
        ),
        prepared_at=prepared_at or datetime.now(),
    )


def prepare_command_dispatch(
    entry: CommandJournalEntry,
    path: str | Path = DEFAULT_STATE_DB,
) -> CommandJournalWriteResult:
    try:
        db_path = initialize_command_journal_db(path)
        with _connect(db_path) as connection:
            return prepare_command_dispatch_in_transaction(entry, connection)
    except sqlite3.IntegrityError as exc:
        return CommandJournalWriteResult(
            persisted=False,
            blocker=f"duplicate command key in command journal: {exc}",
        )
    except OSError as exc:
        return CommandJournalWriteResult(
            persisted=False,
            blocker=f"command journal unavailable: {exc}",
        )
    except sqlite3.Error as exc:
        return CommandJournalWriteResult(
            persisted=False,
            blocker=f"command journal unavailable: {exc}",
        )


def prepare_command_dispatch_in_transaction(
    entry: CommandJournalEntry,
    connection: sqlite3.Connection,
) -> CommandJournalWriteResult:
    ensure_command_journal_table(connection)
    if entry.state != "prepared":
        return CommandJournalWriteResult(
            persisted=False,
            blocker=f"command journal entry is not prepared: {entry.state}",
        )
    existing_row = connection.execute(
        "SELECT payload_json FROM command_journal WHERE journal_id = ?",
        (entry.journal_id,),
    ).fetchone()
    if existing_row is not None:
        existing = _load_entry_payload(
            str(existing_row[0]),
            source="command_journal.payload_json",
        )
        if existing.state != "prepared":
            return CommandJournalWriteResult(
                persisted=False,
                blocker=(
                    "command journal entry already passed pre-dispatch state: "
                    f"{existing.state}"
                ),
            )
        if existing != entry:
            return CommandJournalWriteResult(
                persisted=False,
                blocker="prepared command journal entry conflicts with expected entry",
            )
    try:
        connection.execute(
            """
            INSERT INTO command_journal (
                journal_id, session_id, robot_url, run_id, command_key,
                command_type, state, prepared_at, payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(journal_id) DO UPDATE SET
                session_id = excluded.session_id,
                robot_url = excluded.robot_url,
                run_id = excluded.run_id,
                command_key = excluded.command_key,
                command_type = excluded.command_type,
                state = excluded.state,
                prepared_at = excluded.prepared_at,
                payload_json = excluded.payload_json
            """,
            _entry_row(entry),
        )
    except sqlite3.IntegrityError as exc:
        return CommandJournalWriteResult(
            persisted=False,
            blocker=f"duplicate command key in command journal: {exc}",
        )
    return CommandJournalWriteResult(persisted=True, entry=entry)


def write_command_journal_entry(
    entry: CommandJournalEntry,
    path: str | Path = DEFAULT_STATE_DB,
) -> None:
    db_path = initialize_command_journal_db(path)
    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO command_journal (
                journal_id, session_id, robot_url, run_id, command_key,
                command_type, state, prepared_at, payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(journal_id) DO UPDATE SET
                session_id = excluded.session_id,
                robot_url = excluded.robot_url,
                run_id = excluded.run_id,
                command_key = excluded.command_key,
                command_type = excluded.command_type,
                state = excluded.state,
                prepared_at = excluded.prepared_at,
                payload_json = excluded.payload_json
            """,
            _entry_row(entry),
        )


def read_command_journal_entry(
    journal_id: str,
    path: str | Path = DEFAULT_STATE_DB,
) -> CommandJournalEntry | None:
    db_path = initialize_command_journal_db(path)
    with _connect(db_path) as connection:
        row = connection.execute(
            "SELECT payload_json FROM command_journal WHERE journal_id = ?",
            (journal_id,),
        ).fetchone()
    if row is None:
        return None
    return _load_entry_payload(row[0], source=f"{db_path}:command_journal.payload_json")


def list_command_journal_entries(
    session_id: str,
    path: str | Path = DEFAULT_STATE_DB,
) -> list[CommandJournalEntry]:
    db_path = initialize_command_journal_db(path)
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM command_journal
            WHERE session_id = ?
            ORDER BY prepared_at
            """,
            (session_id,),
        ).fetchall()
    return [
        _load_entry_payload(row[0], source=f"{db_path}:command_journal.payload_json")
        for row in rows
    ]


def mark_command_posted(
    entry: CommandJournalEntry,
    *,
    response: EndpointResult | None = None,
    now: datetime | None = None,
) -> CommandJournalEntry:
    update: dict[str, object] = {
        "state": "posted",
        "posted_at": now or datetime.now(),
    }
    if response is not None:
        update["response_status_code"] = response.status_code
        command = _command_from_response(response)
        if command is not None:
            update.update(_command_update(command))
            if response.ok:
                update["state"] = _state_for_status(
                    _string_or_none(command.get("status")),
                    accepted_state="accepted",
                )
    return entry.model_copy(update=update)


def dispatch_journaled_command(
    *,
    transport: CommandTransport,
    entry: CommandJournalEntry,
    command_path: str,
    command_body: dict[str, Any],
    journal_path: str | Path = DEFAULT_STATE_DB,
    history_path: str | None = None,
) -> CommandDispatchResult:
    route_blocker = _dispatch_route_blocker(entry, command_path, history_path)
    body_blocker = _dispatch_body_blocker(entry, command_body)
    if route_blocker or body_blocker:
        return CommandDispatchResult(
            entry=entry,
            journal_persisted=False,
            posted=False,
            blockers=[blocker for blocker in (route_blocker, body_blocker) if blocker],
        )

    prepared = prepare_command_dispatch(entry, journal_path)
    if not prepared.persisted or prepared.entry is None:
        return CommandDispatchResult(
            entry=entry,
            journal_persisted=False,
            posted=False,
            blockers=[prepared.blocker or "command journal unavailable"],
        )

    dispatching_entry = prepared.entry.model_copy(update={"state": "dispatching"})
    try:
        write_command_journal_entry(dispatching_entry, journal_path)
    except (OSError, sqlite3.Error) as exc:
        return CommandDispatchResult(
            entry=prepared.entry,
            journal_persisted=False,
            posted=False,
            blockers=[f"command journal unavailable before dispatch: {exc}"],
        )

    post_result = transport.post_json(command_path, command_body)
    posted_entry = mark_command_posted(dispatching_entry, response=post_result)
    try:
        write_command_journal_entry(posted_entry, journal_path)
    except (OSError, sqlite3.Error) as exc:
        return CommandDispatchResult(
            entry=posted_entry,
            journal_persisted=False,
            posted=True,
            post_result=post_result,
            blockers=[f"command journal unavailable after dispatch: {exc}"],
        )

    history = transport.get_json(history_path) if history_path is not None else None
    reconciliation = reconcile_command_history(posted_entry, history)
    if reconciliation.entry is not None:
        try:
            write_command_journal_entry(reconciliation.entry, journal_path)
        except (OSError, sqlite3.Error) as exc:
            return CommandDispatchResult(
                entry=reconciliation.entry,
                journal_persisted=False,
                posted=True,
                post_result=post_result,
                reconciliation=reconciliation,
                blockers=[
                    *reconciliation.blockers,
                    f"command journal unavailable during reconciliation: {exc}",
                ],
            )
    return CommandDispatchResult(
        entry=reconciliation.entry or posted_entry,
        journal_persisted=True,
        posted=True,
        post_result=post_result,
        reconciliation=reconciliation,
        blockers=reconciliation.blockers,
    )


def reconcile_command_history(
    entry: CommandJournalEntry | None,
    command_history: EndpointResult | None,
    *,
    now: datetime | None = None,
) -> CommandReconciliationResult:
    if entry is None:
        return CommandReconciliationResult(
            state="recovery_required",
            blockers=["command response has no matching journal entry"],
            recovery_required=True,
        )
    if command_history is None or not command_history.ok:
        return _ambiguous_result(entry, "command history is unavailable", now=now)

    commands = _commands_from_history(command_history)
    if commands is None:
        return _ambiguous_result(entry, "command history payload is malformed", now=now)
    if not _history_is_complete(command_history, commands):
        return _ambiguous_result(entry, "command history payload is incomplete", now=now)
    if _history_path_run_id(command_history.path) != entry.run_id:
        return _ambiguous_result(
            entry,
            "command history run does not match journal entry",
            now=now,
        )

    keyed = [
        (index, command)
        for index, command in enumerate(commands)
        if _string_or_none(command.get("key")) == entry.command_key
    ]
    if len(keyed) > 1:
        return _ambiguous_result(
            entry,
            "duplicate command key is non-idempotent",
            now=now,
            non_idempotent_duplicate_key=True,
        )

    matches = [
        (index, command)
        for index, command in enumerate(commands)
        if _matches_entry(entry, command)
    ]
    if len(matches) != 1:
        return _ambiguous_result(
            entry,
            "command history does not contain exactly one matching command",
            now=now,
        )

    index, command = matches[0]
    status = _string_or_none(command.get("status"))
    state = _state_for_status(status, accepted_state="ambiguous")
    if state in COMMAND_AMBIGUOUS_STATES:
        return _ambiguous_result(
            entry,
            f"command status {status!r} is ambiguous",
            now=now,
            command=command,
            command_index=index,
        )

    reconciled = entry.model_copy(
        update={
            **_command_update(command),
            "command_index": index,
            "state": state,
            "reconciled_at": now or datetime.now(),
            "blockers": [],
        }
    )
    return CommandReconciliationResult(
        entry=reconciled,
        state=state,
        matched_command_id=reconciled.command_id,
        matched_command_index=index,
        command_history_total_length=len(commands),
        matched_command_is_latest=index == len(commands) - 1,
        matched_status=status,
        recovery_required=False,
    )


def apply_command_reconciliation_to_session(
    session: BridgeSession,
    reconciliation: CommandReconciliationResult,
) -> BridgeSession:
    if not reconciliation.recovery_required:
        return session
    notes = [
        *session.notes,
        "Command reconciliation was ambiguous; manual recovery is required.",
    ]
    return session.model_copy(
        update={
            "state": BridgeSessionState.RECOVERY_REQUIRED,
            "motion_allowed": False,
            "updated_at": datetime.now(),
            "notes": notes,
        }
    )


def apply_and_persist_command_reconciliation_to_session(
    session: BridgeSession,
    reconciliation: CommandReconciliationResult,
    path: str | Path = DEFAULT_STATE_DB,
) -> BridgeSession:
    from aevum_ot2.core.sessions import write_session

    updated = apply_command_reconciliation_to_session(session, reconciliation)
    if updated is not session:
        write_session(updated, path)
    return updated


def _connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=FULL")
    return connection


def _entry_row(entry: CommandJournalEntry) -> tuple[str, str, str, str, str, str, str, str, str]:
    return (
        entry.journal_id,
        entry.session_id,
        entry.robot_url,
        entry.run_id,
        entry.command_key,
        entry.command_type,
        entry.state,
        entry.prepared_at.isoformat(),
        entry.model_dump_json(),
    )


def _load_entry_payload(payload_json: str, *, source: str) -> CommandJournalEntry:
    data = loads_json_object(payload_json, schema_name="CommandJournalEntry", path=source)
    return parse_versioned_json_model(
        data,
        CommandJournalEntry,
        schema_name="CommandJournalEntry",
        path=source,
    )


def _command_data(command_body: dict[str, Any]) -> dict[str, Any]:
    data = command_body.get("data")
    if not isinstance(data, dict):
        raise ValueError("command body must contain a data object")
    return data


def _required_command_string(command_data: dict[str, Any], field: str) -> str:
    value = command_data.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"command data must contain non-empty {field}")
    return value


def _stable_command_params_sha256(command_type: str, params: dict[str, Any]) -> str:
    return _stable_json_sha256(_normalized_command_params(command_type, params))


def _normalized_command_params(
    command_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    normalized = json.loads(json.dumps(params, sort_keys=True, separators=(",", ":")))
    if command_type == "moveToWell":
        well_location = normalized.get("wellLocation")
        if isinstance(well_location, dict) and well_location.get("volumeOffset") == 0.0:
            well_location = dict(well_location)
            well_location.pop("volumeOffset", None)
            normalized["wellLocation"] = well_location
    return normalized


def _command_from_response(response: EndpointResult) -> dict[str, Any] | None:
    data = response.data
    if not isinstance(data, dict):
        return None
    command = data.get("data")
    return command if isinstance(command, dict) else None


def _commands_from_history(response: EndpointResult) -> list[dict[str, Any]] | None:
    data = response.data
    if not isinstance(data, dict):
        return None
    commands = data.get("data")
    if not isinstance(commands, list):
        return None
    parsed: list[dict[str, Any]] = []
    for command in commands:
        if not isinstance(command, dict):
            return None
        parsed.append(command)
    return parsed


def _history_is_complete(response: EndpointResult, commands: list[dict[str, Any]]) -> bool:
    data = response.data
    if not isinstance(data, dict):
        return False
    meta = data.get("meta")
    if not isinstance(meta, dict):
        return False
    total_length = meta.get("totalLength")
    if isinstance(total_length, int) and not isinstance(total_length, bool):
        return total_length <= len(commands)
    return False


def _history_path_run_id(path: str) -> str | None:
    route = path.split("?", 1)[0].strip("/")
    parts = route.split("/")
    if len(parts) == 3 and parts[0] == "maintenance_runs" and parts[2] == "commands":
        return parts[1]
    return None


def _dispatch_route_blocker(
    entry: CommandJournalEntry,
    command_path: str,
    history_path: str | None,
) -> str:
    command_run_id = _history_path_run_id(command_path)
    if command_run_id != entry.run_id:
        return "command path run does not match journal entry"
    if history_path is None:
        return "command history path is required for journaled dispatch"
    history_run_id = _history_path_run_id(history_path)
    if history_run_id != entry.run_id:
        return "command history path run does not match journal entry"
    return ""


def _dispatch_body_blocker(
    entry: CommandJournalEntry,
    command_body: dict[str, Any],
) -> str:
    try:
        command_data = _command_data(command_body)
        command_key = _required_command_string(command_data, "key")
        command_type = _required_command_string(command_data, "commandType")
    except ValueError as exc:
        return f"command body does not match journal entry: {exc}"
    command_params = command_data.get("params")
    if not isinstance(command_params, dict):
        command_params = {}
    if command_key != entry.command_key:
        return "command body key does not match journal entry"
    if command_type != entry.command_type:
        return "command body type does not match journal entry"
    if _stable_json_sha256(command_body) != entry.command_body_sha256:
        return "command body hash does not match journal entry"
    if (
        _stable_command_params_sha256(command_type, command_params)
        != entry.command_params_sha256
    ):
        return "command params hash does not match journal entry"
    return ""


def _matches_entry(entry: CommandJournalEntry, command: dict[str, Any]) -> bool:
    command_type = _string_or_none(command.get("commandType"))
    if entry.command_id is not None:
        if _string_or_none(command.get("id")) != entry.command_id:
            return False
        if _string_or_none(command.get("key")) != entry.command_key:
            return False
        if command_type != entry.command_type:
            return False
        params = command.get("params")
        if not isinstance(params, dict):
            params = {}
        return (
            _stable_command_params_sha256(entry.command_type, params)
            == entry.command_params_sha256
        )
    if _string_or_none(command.get("key")) != entry.command_key:
        return False
    if command_type != entry.command_type:
        return False
    params = command.get("params")
    if not isinstance(params, dict):
        params = {}
    return (
        _stable_command_params_sha256(entry.command_type, params)
        == entry.command_params_sha256
    )


def _command_update(command: dict[str, Any]) -> dict[str, object]:
    return {
        "command_id": _string_or_none(command.get("id")),
        "command_status": _string_or_none(command.get("status")),
    }


def _state_for_status(
    status: str | None,
    *,
    accepted_state: CommandJournalState,
) -> CommandJournalState:
    if status in COMMAND_SUCCESS_STATUSES:
        return "completed"
    if status in COMMAND_FAILURE_STATUSES:
        return "failed"
    if status in {"queued", "running"}:
        return accepted_state
    return "ambiguous"


def _ambiguous_result(
    entry: CommandJournalEntry,
    blocker: str,
    *,
    now: datetime | None,
    command: dict[str, Any] | None = None,
    command_index: int | None = None,
    non_idempotent_duplicate_key: bool = False,
) -> CommandReconciliationResult:
    update: dict[str, object] = {
        "state": "recovery_required",
        "reconciled_at": now or datetime.now(),
        "blockers": [*entry.blockers, blocker],
    }
    if command is not None:
        update.update(_command_update(command))
        update["command_index"] = command_index
    reconciled = entry.model_copy(update=update)
    return CommandReconciliationResult(
        entry=reconciled,
        state="recovery_required",
        matched_command_id=reconciled.command_id,
        matched_command_index=reconciled.command_index,
        matched_status=reconciled.command_status,
        blockers=[blocker],
        recovery_required=True,
        non_idempotent_duplicate_key=non_idempotent_duplicate_key,
    )


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


# --- OT-3: physical-event / foreign-command invalidation ---------------------------------

# Command types that physically move the toolhead, handle liquid, or change deck state. A
# foreign command of one of these is the consequential, motion-relevant case. This is an
# INFORMATIONAL classification only: `invalidated` fails closed on ANY foreign command,
# motion-relevant or not — a stray read still proves the run history is not fully ours.
MOTION_RELEVANT_COMMAND_TYPES: frozenset[str] = frozenset(
    {
        "moveToWell",
        "moveToCoordinates",
        "moveRelative",
        "moveToAddressableArea",
        "moveToAddressableAreaForDropTip",
        "moveLabware",
        "home",
        "retractAxis",
        "aspirate",
        "aspirateInPlace",
        "dispense",
        "dispenseInPlace",
        "blowout",
        "blowOutInPlace",
        "dropTip",
        "dropTipInPlace",
        "pickUpTip",
        "touchTip",
    }
)


class ForeignCommand(BaseModel):
    """A single run-history command not accounted for by any authored journal entry."""

    model_config = ConfigDict(extra="forbid")

    index: int
    command_id: str | None = None
    command_key: str | None = None
    command_type: str | None = None
    status: str | None = None
    reason: str
    motion_relevant: bool = False


class CommandHistoryInvalidation(BaseModel):
    """Verdict of the OT-3 foreign-command scan.

    ``invalidated`` is a WITHHOLD-TRUST signal, never a motion grant: True means the run
    history contains a command this bridge cannot account for, or a history this bridge
    could not fully read. It does not say a move is allowed — only that any standing
    authority resting on "the robot did only what we told it" must be re-verified.
    """

    model_config = ConfigDict(extra="forbid")

    invalidated: bool
    run_id: str
    history_total_length: int | None = None
    foreign_commands: list[ForeignCommand] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    @property
    def motion_relevant_foreign(self) -> list[ForeignCommand]:
        return [command for command in self.foreign_commands if command.motion_relevant]


def detect_foreign_commands(
    *,
    authored_entries: Sequence[CommandJournalEntry],
    command_history: EndpointResult | None,
    run_id: str,
) -> CommandHistoryInvalidation:
    """Fail-closed whole-history scan for commands THIS bridge did not author (OT-3).

    ``reconcile_command_history`` answers "did MY command land?"; its
    ``matched_command_is_latest`` flag only notices a foreign command appended AFTER ours.
    A foreign command that executed BEFORE ours — a touchscreen jog, a second HTTP client,
    a replayed idempotency key — leaves ``matched_command_is_latest`` True yet still moved
    the robot. This scans the ENTIRE run history and reports every command not matched by
    an authored journal entry, reusing the SAME id/key/type/params comparison as
    reconciliation (``_matches_entry``) so there is one definition of "ours".

    Matching is 1:1 — each authored entry may vouch for at most ONE history command. A
    surplus command that still matches an already-consumed entry is a non-idempotent
    duplicate of our own command: a replay that physically re-ran the move (project-verified
    on the OT-2 — duplicate maintenance command keys can both succeed). It is reported
    ``non_idempotent_duplicate_key`` and invalidates, exactly as reconcile_command_history's
    duplicate-key guard does, so OT-3 is never more permissive than reconciliation. (Status
    is deliberately NOT compared per-command: the shared ``_matches_entry`` is also used by
    reconciliation, where a live command's status legitimately differs from the prepared
    entry — the 1:1 cardinality pass, not a status check, is what catches a failed-then-
    replayed-succeeded move.)

    Fails closed: any unaccounted command, or any history we cannot fully and unambiguously
    read (unavailable / malformed / incomplete / wrong run), sets ``invalidated=True``. A
    history command whose key collides with one of ours but whose id/type/params diverge is
    reported as ``authored_key_reuse_mismatch`` (a forged or param-diverging key), distinct
    from a wholly ``unauthored_command_key``.
    """
    if command_history is None or not command_history.ok:
        return CommandHistoryInvalidation(
            invalidated=True, run_id=run_id, blockers=["command_history_unavailable"]
        )
    commands = _commands_from_history(command_history)
    if commands is None:
        return CommandHistoryInvalidation(
            invalidated=True, run_id=run_id, blockers=["command_history_malformed"]
        )
    if not _history_is_complete(command_history, commands):
        return CommandHistoryInvalidation(
            invalidated=True,
            run_id=run_id,
            history_total_length=len(commands),
            blockers=["command_history_incomplete"],
        )
    if _history_path_run_id(command_history.path) != run_id:
        return CommandHistoryInvalidation(
            invalidated=True,
            run_id=run_id,
            history_total_length=len(commands),
            blockers=["command_history_run_mismatch"],
        )

    authored_for_run = [entry for entry in authored_entries if entry.run_id == run_id]
    authored_keys = {entry.command_key for entry in authored_for_run}
    # 1:1 cardinality — each authored entry may account for at most one history command. A
    # surplus row that matches an already-consumed entry is a non-idempotent duplicate of
    # our own command, not proof the robot did only what we told it.
    consumed: set[int] = set()
    foreign: list[ForeignCommand] = []
    for index, command in enumerate(commands):
        matched = next(
            (
                entry_index
                for entry_index, entry in enumerate(authored_for_run)
                if entry_index not in consumed and _matches_entry(entry, command)
            ),
            None,
        )
        if matched is not None:
            consumed.add(matched)
            continue
        command_key = _string_or_none(command.get("key"))
        command_type = _string_or_none(command.get("commandType"))
        if any(_matches_entry(entry, command) for entry in authored_for_run):
            # matches one of our commands, but that entry is already spoken for by an
            # earlier history row -> a duplicate physical execution of our own command.
            reason = "non_idempotent_duplicate_key"
        elif command_key is not None and command_key in authored_keys:
            reason = "authored_key_reuse_mismatch"
        else:
            reason = "unauthored_command_key"
        foreign.append(
            ForeignCommand(
                index=index,
                command_id=_string_or_none(command.get("id")),
                command_key=command_key,
                command_type=command_type,
                status=_string_or_none(command.get("status")),
                reason=reason,
                motion_relevant=command_type in MOTION_RELEVANT_COMMAND_TYPES,
            )
        )
    return CommandHistoryInvalidation(
        invalidated=bool(foreign),
        run_id=run_id,
        history_total_length=len(commands),
        foreign_commands=foreign,
    )
