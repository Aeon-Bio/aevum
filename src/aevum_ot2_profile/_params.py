from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import Any

from aevum_cad.labware import build_labware_definition

_DEFAULT_PARAMS_NAME = "p300_poc_fixture.params.json"


@dataclass(frozen=True)
class ParameterSnapshot:
    path: Path
    content: bytes
    sha256: str
    params: dict[str, Any]


@dataclass(frozen=True)
class AevumProfileSnapshot:
    """One immutable Aevum-owned authority snapshot for manifest and policy builders."""

    path: Path
    parameter_bytes: bytes
    params_sha256: str
    params: Mapping[str, Any]
    load_name: str
    nominal_dimensions_mm: tuple[float, float, float]
    labware_definition: Mapping[str, Any]
    labware_definition_bytes: bytes
    labware_definition_sha256: str


def capture_parameter_snapshot(params_path: str | Path | None = None) -> ParameterSnapshot:
    """Open one regular file once, then hash and parse the bytes read from that fd."""

    path = _parameter_path(params_path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ValueError(f"parameter artifact is not a readable regular file: {path}") from exc
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"parameter artifact must be a regular file: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        try:
            path_metadata = os.stat(path, follow_symlinks=False)
        except OSError as exc:
            raise ValueError("parameter artifact changed while it was being captured") from exc
        if (path_metadata.st_dev, path_metadata.st_ino) != (
            metadata.st_dev,
            metadata.st_ino,
        ):
            raise ValueError("parameter artifact changed while it was being captured")
    finally:
        os.close(fd)

    content = b"".join(chunks)
    try:
        parsed = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"parameter artifact is not valid JSON: {path}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("parameter artifact must contain a JSON object")
    return ParameterSnapshot(
        path=path,
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
        params=parsed,
    )


def capture_aevum_profile_snapshot(
    params_path: str | Path | None = None,
) -> AevumProfileSnapshot:
    """Capture, parse, validate, and render Aevum's fixture authority once."""

    parameters = capture_parameter_snapshot(params_path)
    load_name = portable_load_name(parameters.params)
    dimensions = nominal_dimensions(parameters.params)
    definition = build_labware_definition(parameters.params)
    definition_bytes = labware_definition_bytes(definition)
    _validate_labware_definition(
        definition,
        load_name=load_name,
        nominal_dimensions=dimensions,
    )
    return AevumProfileSnapshot(
        path=parameters.path,
        parameter_bytes=parameters.content,
        params_sha256=parameters.sha256,
        params=_deep_freeze_json(parameters.params),
        load_name=load_name,
        nominal_dimensions_mm=dimensions,
        labware_definition=_deep_freeze_json(definition),
        labware_definition_bytes=definition_bytes,
        labware_definition_sha256=hashlib.sha256(definition_bytes).hexdigest(),
    )


def default_parameter_path() -> Path:
    """Resolve the wheel-packaged default resource at call time."""

    resource = resources.files("aevum_ot2_profile").joinpath(_DEFAULT_PARAMS_NAME)
    if not resource.is_file():
        raise FileNotFoundError(f"packaged parameter artifact is missing: {_DEFAULT_PARAMS_NAME}")
    try:
        return Path(resource)
    except TypeError as exc:
        raise RuntimeError("aevum_ot2_profile must be installed as an unpacked wheel") from exc


def _parameter_path(params_path: str | Path | None) -> Path:
    selected = default_parameter_path() if params_path is None else Path(params_path).expanduser()
    if not str(selected).strip():
        raise ValueError("params_path must be a non-empty path")
    return selected.absolute()


def portable_load_name(params: dict[str, Any]) -> str:
    import re

    portable_segment = re.compile(
        r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?\Z"
    )
    windows_reserved_names = {
        "aux",
        "con",
        "nul",
        "prn",
        *(f"com{index}" for index in range(1, 10)),
        *(f"lpt{index}" for index in range(1, 10)),
    }
    labware = params.get("labware")
    load_name = labware.get("load_name") if isinstance(labware, dict) else None
    if (
        not isinstance(load_name, str)
        or load_name in {".", ".."}
        or portable_segment.fullmatch(load_name) is None
        or load_name.split(".", 1)[0].casefold() in windows_reserved_names
    ):
        raise ValueError("labware load_name must be one portable filename segment")
    return load_name


def nominal_dimensions(params: dict[str, Any]) -> tuple[float, float, float]:
    """Derive and validate design dimensions without trusting labware JSON."""

    try:
        base = params["base"]
        stack = params["raised_stack"]
        mat = params["mat_plane"]
        x_mm = base["length_x"]
        y_mm = base["width_y"]
        z_mm = (
            stack["height_to_mock_plate_top"]
            + mat["height_above_mock_plate_top"]
            + mat["frame_thickness"]
        )
    except (KeyError, TypeError) as exc:
        raise ValueError("Aevum nominal dimensions require CAD base/stack/mat fields") from exc
    return (
        _finite_positive_dimension(x_mm, "nominal x dimension"),
        _finite_positive_dimension(y_mm, "nominal y dimension"),
        _finite_positive_dimension(z_mm, "nominal z dimension"),
    )


def labware_definition_bytes(definition: dict[str, Any]) -> bytes:
    try:
        return (json.dumps(definition, indent=2) + "\n").encode()
    except (TypeError, ValueError) as exc:
        raise ValueError("generated labware definition must be JSON serializable") from exc


def _validate_labware_definition(
    definition: dict[str, Any],
    *,
    load_name: str,
    nominal_dimensions: tuple[float, float, float],
) -> None:
    parameters = definition.get("parameters")
    if not isinstance(parameters, dict) or parameters.get("loadName") != load_name:
        raise ValueError("generated labware loadName does not match captured params")
    dimensions = definition.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("generated labware definition is missing dimensions")
    generated = (
        _finite_positive_dimension(dimensions.get("xDimension"), "labware x dimension"),
        _finite_positive_dimension(dimensions.get("yDimension"), "labware y dimension"),
        _finite_positive_dimension(dimensions.get("zDimension"), "labware z dimension"),
    )
    if generated != nominal_dimensions:
        raise ValueError("generated labware dimensions do not match nominal dimensions")


def _finite_positive_dimension(value: object, label: str) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{label} must be a finite positive number")
    dimension = float(value)
    if not math.isfinite(dimension) or dimension <= 0:
        raise ValueError(f"{label} must be a finite positive number")
    return dimension


def _deep_freeze_json(value: Any) -> Any:
    """Return a recursively immutable view of captured JSON authority."""

    if isinstance(value, dict):
        return MappingProxyType({key: _deep_freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze_json(item) for item in value)
    return value
