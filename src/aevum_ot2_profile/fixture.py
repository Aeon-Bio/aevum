from __future__ import annotations

import errno
import os
import secrets
import stat
from pathlib import Path

from ot2_harness.core.artifacts import FixtureManifest

from aevum_ot2_profile._params import (
    AevumProfileSnapshot,
    capture_aevum_profile_snapshot,
)


def build_fixture_manifest(
    output_dir: str | Path,
    *,
    params_path: str | Path | None = None,
    snapshot: AevumProfileSnapshot | None = None,
) -> FixtureManifest:
    """Generate caller-scoped labware and bind it to independent CAD authority."""

    active = _active_snapshot(snapshot=snapshot, params_path=params_path)
    root, directory_fd = _open_output_directory(output_dir)
    destination_name = f"{active.load_name}.json"
    try:
        manifest = FixtureManifest(
            schema_version=1,
            labware_path=root / destination_name,
            design_artifact_path=active.path,
            labware_sha256=active.labware_definition_sha256,
            design_artifact_sha256=active.params_sha256,
            nominal_x_mm=active.nominal_dimensions_mm[0],
            nominal_y_mm=active.nominal_dimensions_mm[1],
            nominal_z_mm=active.nominal_dimensions_mm[2],
        )
    except Exception:
        os.close(directory_fd)
        raise
    _publish_labware(directory_fd, destination_name, active.labware_definition_bytes)
    return manifest


def _active_snapshot(
    *,
    snapshot: AevumProfileSnapshot | None,
    params_path: str | Path | None,
) -> AevumProfileSnapshot:
    if snapshot is not None and params_path is not None:
        raise ValueError("provide either snapshot or params_path, not both")
    return snapshot if snapshot is not None else capture_aevum_profile_snapshot(params_path)


def _open_output_directory(output_dir: str | Path) -> tuple[Path, int]:
    if not str(output_dir).strip():
        raise ValueError("output_dir must be a non-empty caller-scoped path")
    requested = Path(output_dir).expanduser().absolute()
    try:
        metadata = requested.lstat()
    except OSError as exc:
        raise ValueError("output_dir must be a caller-created physical directory") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("output_dir must be a real directory, not a symlink")
    physical_root = requested.resolve(strict=True)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        directory_fd = os.open(requested, flags)
    except OSError as exc:
        raise ValueError("output_dir must remain a physical directory") from exc
    opened = os.fstat(directory_fd)
    if not stat.S_ISDIR(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
        metadata.st_dev,
        metadata.st_ino,
    ):
        os.close(directory_fd)
        raise ValueError("output_dir changed while it was being opened")
    return physical_root, directory_fd


def _publish_labware(
    directory_fd: int,
    destination_name: str,
    content: bytes,
) -> None:
    temporary_name = f".{destination_name}.{secrets.token_hex(12)}.tmp"
    temporary_created = False
    try:
        try:
            os.stat(destination_name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError(f"refusing to replace existing destination: {destination_name}")

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        temporary_fd = os.open(temporary_name, flags, 0o600, dir_fd=directory_fd)
        temporary_created = True
        try:
            view = memoryview(content)
            while view:
                written = os.write(temporary_fd, view)
                if written <= 0:
                    raise OSError("short write while publishing labware definition")
                view = view[written:]
            os.fsync(temporary_fd)
        finally:
            os.close(temporary_fd)

        try:
            os.link(
                temporary_name,
                destination_name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                raise FileExistsError(
                    f"refusing to replace competing destination: {destination_name}"
                ) from exc
            raise
        os.unlink(temporary_name, dir_fd=directory_fd)
        temporary_created = False
        os.fsync(directory_fd)
    finally:
        if temporary_created:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        os.close(directory_fd)
