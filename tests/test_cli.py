from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import typer

from aevum_ot2.adapters import cli
from aevum_ot2.adapters.cli import (
    _default_legacy_image_evidence_output,
    _fixture_qc_scope,
    _pose_authority_claims,
    _target_class_record_paths,
)
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.models import EvidenceClaim, EvidenceQuality


def test_default_legacy_image_evidence_output_is_purpose_and_image_scoped() -> None:
    output = _default_legacy_image_evidence_output(
        Path("fixture image.jpg"),
        "fixture_presence",
    )

    assert output.parent.as_posix() == "data/measurements/legacy_image_evidence"
    assert output.name.endswith("_fixture_presence_fixture_image.json")


def test_fixture_qc_scope_uses_session_identity_and_pose_digest(monkeypatch) -> None:
    identity = current_fixture_identity()
    session = SimpleNamespace(
        fixture_identity=identity,
        fixture_pose_digest_sha256="a" * 64,
    )
    monkeypatch.setattr(cli, "read_session", lambda session_id: session)

    scoped_identity, pose_digest = _fixture_qc_scope(
        session_id="session-1",
        pose_digest_sha256="",
    )

    assert scoped_identity == identity
    assert pose_digest == "a" * 64


def test_fixture_qc_scope_rejects_mismatched_explicit_pose_digest(monkeypatch) -> None:
    identity = current_fixture_identity()
    session = SimpleNamespace(
        fixture_identity=identity,
        fixture_pose_digest_sha256="a" * 64,
    )
    monkeypatch.setattr(cli, "read_session", lambda session_id: session)

    with pytest.raises(typer.BadParameter, match="does not match session"):
        _fixture_qc_scope(session_id="session-1", pose_digest_sha256="b" * 64)


def test_target_class_record_paths_can_load_scoped_directory(tmp_path) -> None:
    first = tmp_path / "center_high_z.json"
    second = tmp_path / "center_low_z_dry.json"
    ignored = tmp_path / "README.md"
    first.write_text("{}")
    second.write_text("{}")
    ignored.write_text("not a target record")

    paths = _target_class_record_paths([second], tmp_path)

    assert paths == [second, first]


def test_target_class_record_paths_rejects_empty_directory(tmp_path) -> None:
    with pytest.raises(typer.BadParameter, match="contains no JSON records"):
        _target_class_record_paths(None, tmp_path)


def test_pose_authority_claims_filters_non_pose_claims() -> None:
    pose_claim = EvidenceClaim(
        claim_id="pose-upright",
        claim_type="fixture_upright",
        value=True,
        method="fixture_pose_evidence_packet_v1",
        quality=EvidenceQuality.USABLE,
    )
    orientation_claim = EvidenceClaim(
        claim_id="pose-orientation",
        claim_type="fixture_pose_orientation:rot180:slot-5",
        value=True,
        method="fixture_pose_evidence_packet_v1",
        quality=EvidenceQuality.USABLE,
    )
    target_claim = EvidenceClaim(
        claim_id="target-class",
        claim_type="target_class_verified:center_high_z",
        value=True,
        method="target_class_evidence_packet_v1",
        quality=EvidenceQuality.USABLE,
    )

    assert _pose_authority_claims([pose_claim, target_claim, orientation_claim]) == [
        pose_claim,
        orientation_claim,
    ]
