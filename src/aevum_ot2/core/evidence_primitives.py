"""Canonical, single-source evidence primitives shared across the OT-2 evidence modules.

These six helpers were previously copy-pasted into target_evidence.py, pose_evidence.py,
high_z_motion_evidence.py, records.py, pose.py, evidence.py, and motion_approval.py (4-6
copies each). Two of them encode SHARED INVARIANTS that MUST stay identical everywhere:
``_safe_path_segment`` is the path-traversal guard, and ``_transaction_root_for_index``
encodes the on-disk transaction layout. In a tamper-evidence system, a hardening fix that
lands in some copies but not others is a silent forgery surface — so they live here once.

This module is a graph SINK: it imports ONLY the standard library, so nothing in
``aevum_ot2.core`` can ever form an import cycle through it. Every evidence module points
DOWN to this leaf.

The leading-underscore names are kept so existing call sites are untouched; the module is the
shared internal kernel for the evidence layer, not a public API.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

# The on-disk directory name for committed evidence transactions. The single source of this
# token; the path is DERIVED from different anchors in different layers (the session evidence
# index in core, the state-db path in the server), but the name itself must not drift.
EVIDENCE_TRANSACTIONS_DIRNAME = "evidence_transactions"


def _stable_json_sha256(value: object) -> str:
    """SHA-256 over a canonical JSON encoding (sorted keys, compact separators, UTF-8).

    The single source of the stable-JSON digest used for command-body/params hashes, the
    fixture-safety-profile digest, and (via a caller-applied canonicalization) the pose
    digest. The encoding (``sort_keys=True``, ``separators=(",", ":")``, UTF-8) is
    DIGEST-LOAD-BEARING — these hashes are persisted and compared across runs, so the exact
    byte encoding must never change. Callers that need domain canonicalization apply it to
    ``value`` BEFORE calling this (e.g. pose passes ``_canonicalize(payload)``).
    """
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    """Stream a file through SHA-256 in 1 MiB chunks (constant memory)."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_path_segment(value: str) -> str:
    """Sanitize a string into a single filesystem path segment (path-traversal guard).

    Replaces every character outside ``[alnum, -, _]`` with ``_`` and strips leading/trailing
    ``_``; raises if nothing path-safe remains. SECURITY-relevant: the allowed-character set
    and the fail-closed ValueError are load-bearing — do not loosen them.
    """
    safe = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in value
    ).strip("_")
    if not safe:
        raise ValueError("session_id must contain at least one path-safe character")
    return safe


def _same_path(left: object, right: object) -> bool:
    """Whether two path-like values denote the same path (fail-closed on non-path input).

    Reconciled from two prior divergent copies. Some call sites pass UNTRUSTED dict lookups
    (``payload.get("image_path")``) that can be ``None`` or a non-path type — those must fail
    closed (return False), never crash. Other call sites pass a real ``Path`` for one argument
    — those must be accepted, not rejected. So the guard admits exactly ``str`` and ``Path``
    and returns False for anything else; the OSError fallback compares the string forms (which
    is equivalent to comparing the Paths for any real path input).
    """
    if not isinstance(left, (str, Path)) or not isinstance(right, (str, Path)):
        return False
    left_path = Path(left)
    right_path = Path(right)
    try:
        return left_path.resolve() == right_path.resolve()
    except OSError:
        return str(left_path) == str(right_path)


def _is_timezone_aware(value: datetime) -> bool:
    """Whether a datetime carries an effective UTC offset (both clauses are load-bearing)."""
    return value.tzinfo is not None and value.utcoffset() is not None


def _datetime_payload(value: datetime | None) -> str:
    """ISO-8601 string for a datetime, or "" for None — the canonical payload encoding."""
    return value.isoformat() if value is not None else ""


def _transaction_root_for_index(index_path: Path) -> Path:
    """Resolve the evidence-transactions root from a session evidence index path.

    Encodes the on-disk layout invariant ``<root>/evidence_transactions`` two directories up
    from the session index; the ``< 3`` depth check and the ``parents[2]`` index are
    load-bearing and must stay identical everywhere.
    """
    if len(index_path.parents) < 3:
        raise ValueError("session evidence index path is too shallow")
    return index_path.parents[2] / EVIDENCE_TRANSACTIONS_DIRNAME
