from __future__ import annotations

from pathlib import Path

from ot2_harness.core.config import WorkspacePaths


def build_workspace_paths(repository_root: str | Path) -> WorkspacePaths:
    """Describe Aevum's established durable locations without creating them."""

    if not str(repository_root).strip():
        raise ValueError("repository_root must be an explicit non-empty Aevum workspace path")
    workspace = Path(repository_root).expanduser().resolve()
    measurements = workspace / "data" / "measurements"
    sessions = measurements / "sessions"
    return WorkspacePaths(
        workspace=workspace,
        state_db=measurements / "ot2_bridge_state.sqlite3",
        evidence_index=measurements / "ot2_evidence_index.json",
        evidence_transactions=measurements / "evidence_transactions",
        sessions=sessions,
        poses=sessions,
        offset_registry=measurements / "ot2_offset_registry.json",
        images=measurements / "images",
        target_scaffolds=measurements / "target_classes",
        fixture_qc=measurements / "fixture_qc.json",
        safety_profiles=measurements / "safety_profiles",
        legacy_evidence=measurements / "legacy_image_evidence",
    )
