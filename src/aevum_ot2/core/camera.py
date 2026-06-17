from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from aevum_cad.params import ROOT
from aevum_ot2.core.evidence import DEFAULT_EVIDENCE_INDEX, append_evidence_event
from aevum_ot2.core.models import CameraCaptureResult, EvidenceEvent

DEFAULT_IMAGE_DIR = ROOT / "data" / "measurements" / "images"


def capture_picture(
    robot_url: str,
    *,
    output_dir: str | Path = DEFAULT_IMAGE_DIR,
    filename: str | None = None,
    timeout_seconds: float = 20.0,
    record_evidence: bool = True,
    evidence_index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    session_id: str | None = None,
) -> CameraCaptureResult:
    """Capture a still image through the non-run OT-2 camera endpoint."""

    requested_at = datetime.now()
    image_dir = Path(output_dir)
    image_dir.mkdir(parents=True, exist_ok=True)
    image_name = filename or f"aevum_camera_picture_{requested_at:%Y-%m-%d_%H%M%S}.jpg"
    image_path = image_dir / _safe_image_name(image_name)
    endpoint = "/camera/picture"

    request = Request(
        urljoin(robot_url.rstrip("/") + "/", endpoint.lstrip("/")),
        headers={
            "Accept": "image/jpg",
            "Opentrons-Version": "*",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            content = response.read()
            content_type = response.headers.get("Content-Type")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"camera capture failed: HTTP {exc.code}: {detail}") from exc
    except (TimeoutError, URLError, OSError) as exc:
        raise RuntimeError(f"camera capture failed: {exc}") from exc

    image_path.write_bytes(content)
    captured_at = datetime.now()
    image_checksum = _sha256_bytes(content)
    result = CameraCaptureResult(
        robot_url=robot_url.rstrip("/"),
        captured_at=captured_at,
        endpoint=endpoint,
        image_path=str(image_path),
        image_checksum_sha256=image_checksum,
        content_type=content_type,
        bytes_written=len(content),
    )

    if record_evidence:
        append_evidence_event(
            EvidenceEvent(
                event_type="ot2_camera_picture",
                session_id=session_id,
                summary=f"Captured OT-2 camera image from {robot_url}",
                payload=result.model_dump(mode="json"),
            ),
            path=evidence_index_path,
        )

    return result


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _safe_image_name(filename: str) -> str:
    path = Path(filename)
    if path.is_absolute() or path.name != filename:
        raise ValueError("camera capture filename must be a plain file name")
    return filename
