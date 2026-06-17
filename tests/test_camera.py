from __future__ import annotations

import pytest

from aevum_ot2.core.camera import capture_picture


def test_camera_capture_rejects_path_filename(tmp_path) -> None:
    with pytest.raises(ValueError, match="plain file name"):
        capture_picture(
            "http://ot2.local:31950",
            output_dir=tmp_path,
            filename="../escape.jpg",
            record_evidence=False,
        )
