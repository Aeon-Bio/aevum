from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from PIL import Image, ImageFilter, ImageStat, UnidentifiedImageError

from aevum_ot2.core.evidence import DEFAULT_EVIDENCE_INDEX, append_evidence_event
from aevum_ot2.core.models import EvidenceEvent, ImageMetrics, VisionAnalysisResult, VisionCheck

VisionPurpose = Literal["deck_baseline", "fixture_presence", "high_z_target", "recovery"]

MIN_CAMERA_WIDTH_PX = 640
MIN_CAMERA_HEIGHT_PX = 480
MIN_MEAN_LUMA = 20.0
MAX_MEAN_LUMA = 235.0
MIN_LUMA_STDDEV = 8.0
MIN_EDGE_MEAN = 1.0
MOTION_BLOCKED_SUMMARY = "image recorded; vision gate does not authorize motion"


def analyze_camera_image(
    image_path: str | Path,
    *,
    purpose: VisionPurpose = "deck_baseline",
    record_evidence: bool = True,
    evidence_index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
) -> VisionAnalysisResult:
    """Analyze a camera still for evidence quality without authorizing motion."""

    path = Path(image_path)
    analyzed_at = datetime.now()
    checks: list[VisionCheck] = []

    try:
        with Image.open(path) as image:
            image.load()
            metrics = _measure_image(image)
    except FileNotFoundError:
        result = _failed_result(
            path=path,
            analyzed_at=analyzed_at,
            purpose=purpose,
            details="image file does not exist",
        )
        return _record_if_needed(result, record_evidence, evidence_index_path)
    except UnidentifiedImageError:
        result = _failed_result(
            path=path,
            analyzed_at=analyzed_at,
            purpose=purpose,
            details="image file is not a recognized image",
        )
        return _record_if_needed(result, record_evidence, evidence_index_path)
    except OSError as exc:
        result = _failed_result(
            path=path,
            analyzed_at=analyzed_at,
            purpose=purpose,
            details=f"image file could not be read: {exc}",
        )
        return _record_if_needed(result, record_evidence, evidence_index_path)

    checks.extend(_quality_checks(metrics))
    if purpose in {"fixture_presence", "high_z_target"}:
        checks.append(
            VisionCheck(
                name="validated_fixture_detector",
                passed=False,
                severity="blocker",
                details=(
                    "fixture/fiducial detector has not been calibrated with installed-fixture "
                    "evidence"
                ),
                observed=False,
                threshold=True,
            )
        )

    non_evidence_blockers = {"motion_authorization", "validated_fixture_detector"}
    evidence_blockers = [
        check
        for check in checks
        if not check.passed
        and check.severity == "blocker"
        and check.name not in non_evidence_blockers
    ]
    evidence_ok = not evidence_blockers
    result = VisionAnalysisResult(
        image_path=str(path),
        analyzed_at=analyzed_at,
        purpose=purpose,
        metrics=metrics,
        evidence_ok=evidence_ok,
        motion_gate=False,
        checks=checks,
        summary=_summary(evidence_ok=evidence_ok, purpose=purpose),
    )
    return _record_if_needed(result, record_evidence, evidence_index_path)


def _measure_image(image: Image.Image) -> ImageMetrics:
    rgb = image.convert("RGB")
    luma = rgb.convert("L")
    luma_stats = ImageStat.Stat(luma)
    edge_image = luma.filter(ImageFilter.FIND_EDGES)
    edge_stats = ImageStat.Stat(edge_image)

    return ImageMetrics(
        width_px=rgb.width,
        height_px=rgb.height,
        mode=image.mode,
        mean_luma=round(float(luma_stats.mean[0]), 3),
        luma_stddev=round(float(luma_stats.stddev[0]), 3),
        edge_mean=round(float(edge_stats.mean[0]), 3),
    )


def _quality_checks(metrics: ImageMetrics) -> list[VisionCheck]:
    return [
        VisionCheck(
            name="minimum_resolution",
            passed=(
                metrics.width_px >= MIN_CAMERA_WIDTH_PX
                and metrics.height_px >= MIN_CAMERA_HEIGHT_PX
            ),
            severity="blocker",
            details="image meets minimum OT-2 still capture resolution",
            observed=f"{metrics.width_px}x{metrics.height_px}",
            threshold=f"{MIN_CAMERA_WIDTH_PX}x{MIN_CAMERA_HEIGHT_PX}",
        ),
        VisionCheck(
            name="not_underexposed",
            passed=metrics.mean_luma >= MIN_MEAN_LUMA,
            severity="blocker",
            details="mean luminance is high enough for evidence review",
            observed=metrics.mean_luma,
            threshold=MIN_MEAN_LUMA,
        ),
        VisionCheck(
            name="not_overexposed",
            passed=metrics.mean_luma <= MAX_MEAN_LUMA,
            severity="blocker",
            details="mean luminance is low enough to avoid washed-out evidence",
            observed=metrics.mean_luma,
            threshold=MAX_MEAN_LUMA,
        ),
        VisionCheck(
            name="minimum_contrast",
            passed=metrics.luma_stddev >= MIN_LUMA_STDDEV,
            severity="blocker",
            details="image contrast is high enough for coarse scene evidence",
            observed=metrics.luma_stddev,
            threshold=MIN_LUMA_STDDEV,
        ),
        VisionCheck(
            name="minimum_structure",
            passed=metrics.edge_mean >= MIN_EDGE_MEAN,
            severity="warning",
            details="edge response suggests visible deck structure",
            observed=metrics.edge_mean,
            threshold=MIN_EDGE_MEAN,
        ),
        VisionCheck(
            name="motion_authorization",
            passed=False,
            severity="blocker",
            details=(
                "this first-pass vision analysis records evidence only and cannot authorize "
                "motion"
            ),
            observed=False,
            threshold=True,
        ),
    ]


def _failed_result(
    *,
    path: Path,
    analyzed_at: datetime,
    purpose: VisionPurpose,
    details: str,
) -> VisionAnalysisResult:
    return VisionAnalysisResult(
        image_path=str(path),
        analyzed_at=analyzed_at,
        purpose=purpose,
        evidence_ok=False,
        motion_gate=False,
        checks=[
            VisionCheck(
                name="image_readable",
                passed=False,
                severity="blocker",
                details=details,
            )
        ],
        summary="image analysis failed; motion remains blocked",
    )


def _summary(*, evidence_ok: bool, purpose: VisionPurpose) -> str:
    if evidence_ok and purpose == "deck_baseline":
        return MOTION_BLOCKED_SUMMARY
    if evidence_ok:
        return "image recorded for commissioning; calibrated detector is still required"
    return "image quality failed; motion remains blocked"


def _record_if_needed(
    result: VisionAnalysisResult,
    record_evidence: bool,
    evidence_index_path: str | Path,
) -> VisionAnalysisResult:
    if record_evidence:
        append_evidence_event(
            EvidenceEvent(
                event_type="ot2_camera_vision_analysis",
                summary=result.summary,
                payload=result.model_dump(mode="json"),
            ),
            path=evidence_index_path,
        )
    return result
