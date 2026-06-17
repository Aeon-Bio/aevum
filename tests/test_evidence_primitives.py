"""Lock the canonical evidence primitives — especially the reconciled `_same_path`.

These were consolidated from 4-6 duplicate copies across `core/` into one home. The tests
pin the security-relevant invariants (`_safe_path_segment` traversal guard,
`_transaction_root_for_index` layout) and the one behavior-bearing reconciliation
(`_same_path`, which merged a fail-closed object-guard variant and a str|Path variant).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aevum_ot2.core.evidence_primitives import (
    EVIDENCE_TRANSACTIONS_DIRNAME,
    _datetime_payload,
    _is_timezone_aware,
    _safe_path_segment,
    _same_path,
    _sha256_file,
    _stable_json_sha256,
    _transaction_root_for_index,
)

# --- _same_path: the reconciliation of the two prior divergent variants -------------------


def test_same_path_fails_closed_on_untrusted_non_path() -> None:
    # The object-variant call sites (evidence.py/pose.py) pass untrusted dict lookups that can
    # be None or non-str; those MUST fail closed (False), never crash (Path(None) raises).
    assert _same_path(None, "x") is False
    assert _same_path("x", None) is False
    assert _same_path(None, None) is False
    assert _same_path(123, "x") is False
    assert _same_path(b"bytes", "x") is False


def test_same_path_accepts_str_and_path() -> None:
    # The str|Path call sites pass a real Path for one argument; it must be ACCEPTED, not
    # rejected by a str-only guard (that was the latent narrowing bug in the object variant).
    assert _same_path("/a/b", "/a/b") is True
    assert _same_path(Path("/a/b"), "/a/b") is True
    assert _same_path("/a/b", Path("/a/b")) is True
    assert _same_path(Path("/a/b"), Path("/a/b")) is True


def test_same_path_distinguishes_different_paths() -> None:
    assert _same_path("/a/b", "/a/c") is False
    assert _same_path(Path("/a/b"), Path("/a/c")) is False


def test_same_path_normalizes_equivalent_strings() -> None:
    # Path normalization collapses redundant separators; equivalent forms compare equal.
    assert _same_path("/a//b", "/a/b") is True


# --- _safe_path_segment: the path-traversal guard -----------------------------------------


def test_safe_path_segment_sanitizes_traversal_and_separators() -> None:
    assert _safe_path_segment("../../etc/passwd") == "etc_passwd"
    assert _safe_path_segment("a/b\\c") == "a_b_c"
    assert _safe_path_segment("sess-1_ok") == "sess-1_ok"  # allowed chars preserved
    assert _safe_path_segment("..%2f..") == "2f"


def test_safe_path_segment_rejects_all_unsafe() -> None:
    with pytest.raises(ValueError, match="at least one path-safe character"):
        _safe_path_segment("/////")
    with pytest.raises(ValueError, match="at least one path-safe character"):
        _safe_path_segment("...")


# --- _transaction_root_for_index: the on-disk layout invariant ----------------------------


def test_transaction_root_is_two_dirs_up(tmp_path: Path) -> None:
    index = tmp_path / "sessions" / "session-1" / "evidence_index.json"
    assert _transaction_root_for_index(index) == tmp_path / "evidence_transactions"


def test_transaction_root_rejects_shallow_path() -> None:
    with pytest.raises(ValueError, match="too shallow"):
        _transaction_root_for_index(Path("evidence_index.json"))


# --- _sha256_file / _is_timezone_aware / _datetime_payload --------------------------------


def test_sha256_file_matches_hashlib(tmp_path: Path) -> None:
    f = tmp_path / "blob.bin"
    f.write_bytes(b"observer-evidence-bytes" * 100)
    assert _sha256_file(f) == hashlib.sha256(f.read_bytes()).hexdigest()


def test_is_timezone_aware() -> None:
    assert _is_timezone_aware(datetime.now(tz=UTC)) is True
    assert _is_timezone_aware(datetime(2026, 6, 17, 12, 0, 0)) is False


def test_datetime_payload() -> None:
    assert _datetime_payload(None) == ""
    naive = datetime(2026, 6, 17, 12, 0, 0)
    assert _datetime_payload(naive) == naive.isoformat()


# --- _stable_json_sha256: the DIGEST-LOAD-BEARING canonical JSON hash ----------------------


def test_stable_json_sha256_pins_exact_encoding() -> None:
    # The encoding (sort_keys + compact separators + UTF-8) is persisted and compared across
    # runs; pin it to the literal bytes so an accidental change to canonicalization goes red.
    payload = {"b": 1, "a": [3, 2]}
    expected = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert _stable_json_sha256(payload) == expected


def test_stable_json_sha256_is_key_order_invariant() -> None:
    assert _stable_json_sha256({"a": 1, "b": 2}) == _stable_json_sha256({"b": 2, "a": 1})


def test_evidence_transactions_dirname_is_the_single_token() -> None:
    assert EVIDENCE_TRANSACTIONS_DIRNAME == "evidence_transactions"
    # _transaction_root_for_index derives its path from this constant
    root = _transaction_root_for_index(Path("/x/y/z/sessions/s1/evidence_index.json"))
    assert root.name == EVIDENCE_TRANSACTIONS_DIRNAME


def test_stable_json_sha256_golden_vector() -> None:
    # Hardcoded golden digest: a SYMMETRIC byte-level encoding change (applied on both write
    # and verify, which round-trip tests would miss) flips this. Pins the exact canonical bytes
    # of every persisted digest routed through _stable_json_sha256.
    assert _stable_json_sha256({"z": [1, 2], "a": "x", "m": True}) == (
        "bfa9bd43bef87221f5dbc00a3551d3c0d4f34cfd7542cdb0e7ec8189bf06ab99"
    )
