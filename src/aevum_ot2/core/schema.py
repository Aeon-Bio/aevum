from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

CURRENT_SCHEMA_VERSION = 1

_MISSING = object()
ModelT = TypeVar("ModelT", bound=BaseModel)


class SchemaVersionError(ValueError):
    def __init__(
        self,
        *,
        schema_name: str,
        expected_version: int,
        actual_version: object = _MISSING,
        path: str | Path | None = None,
        reason: str = "",
    ) -> None:
        self.schema_name = schema_name
        self.expected_version = expected_version
        self.actual_version = actual_version
        self.path = None if path is None else str(path)
        message_path = "" if self.path is None else f" at {self.path}"
        if reason:
            message = f"{schema_name}{message_path} {reason}"
        elif actual_version is _MISSING:
            message = (
                f"{schema_name}{message_path} is missing schema_version; "
                f"expected {expected_version}"
            )
        else:
            message = (
                f"{schema_name}{message_path} has unsupported schema_version "
                f"{actual_version!r}; expected {expected_version}"
            )
        super().__init__(message)


def loads_json_object(
    text: str,
    *,
    schema_name: str,
    path: str | Path | None = None,
) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SchemaVersionError(
            schema_name=schema_name,
            expected_version=CURRENT_SCHEMA_VERSION,
            path=path,
            reason=f"is not valid JSON: {exc.msg}",
        ) from exc
    if not isinstance(data, dict):
        raise SchemaVersionError(
            schema_name=schema_name,
            expected_version=CURRENT_SCHEMA_VERSION,
            path=path,
            reason="must be a JSON object with schema_version",
        )
    return data


def load_json_object(path: str | Path, *, schema_name: str) -> dict[str, Any]:
    json_path = Path(path)
    return loads_json_object(json_path.read_text(), schema_name=schema_name, path=json_path)


def require_schema_version(
    data: Mapping[str, Any],
    *,
    schema_name: str,
    expected_version: int = CURRENT_SCHEMA_VERSION,
    path: str | Path | None = None,
) -> None:
    version = data.get("schema_version", _MISSING)
    if version is _MISSING:
        raise SchemaVersionError(
            schema_name=schema_name,
            expected_version=expected_version,
            path=path,
        )
    if isinstance(version, bool) or not isinstance(version, int) or version != expected_version:
        raise SchemaVersionError(
            schema_name=schema_name,
            expected_version=expected_version,
            actual_version=version,
            path=path,
        )


def require_optional_schema_version(
    data: Mapping[str, Any],
    *,
    schema_name: str,
    expected_version: int = CURRENT_SCHEMA_VERSION,
    path: str | Path | None = None,
) -> None:
    if "schema_version" not in data:
        return
    require_schema_version(
        data,
        schema_name=schema_name,
        expected_version=expected_version,
        path=path,
    )


def require_optional_schema_versioned_items(
    items: object,
    *,
    schema_name: str,
    expected_version: int = CURRENT_SCHEMA_VERSION,
    path: str | Path | None = None,
) -> None:
    if not isinstance(items, Iterable) or isinstance(items, (str, bytes, dict)):
        return
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            continue
        require_optional_schema_version(
            item,
            schema_name=f"{schema_name}[{index}]",
            expected_version=expected_version,
            path=path,
        )


def require_schema_versioned_items(
    items: object,
    *,
    schema_name: str,
    expected_version: int = CURRENT_SCHEMA_VERSION,
    path: str | Path | None = None,
) -> None:
    if not isinstance(items, Iterable) or isinstance(items, (str, bytes, dict)):
        return
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            continue
        require_schema_version(
            item,
            schema_name=f"{schema_name}[{index}]",
            expected_version=expected_version,
            path=path,
        )


def parse_versioned_json_model(
    data: Mapping[str, Any],
    model_type: type[ModelT],
    *,
    schema_name: str,
    expected_version: int = CURRENT_SCHEMA_VERSION,
    path: str | Path | None = None,
) -> ModelT:
    if not isinstance(data, Mapping):
        raise SchemaVersionError(
            schema_name=schema_name,
            expected_version=expected_version,
            path=path,
            reason="must be a JSON object with schema_version",
        )
    require_schema_version(
        data,
        schema_name=schema_name,
        expected_version=expected_version,
        path=path,
    )
    return model_type.model_validate(data)


def load_versioned_json_model(
    path: str | Path,
    model_type: type[ModelT],
    *,
    schema_name: str,
    expected_version: int = CURRENT_SCHEMA_VERSION,
) -> ModelT:
    data = load_json_object(path, schema_name=schema_name)
    return parse_versioned_json_model(
        data,
        model_type,
        schema_name=schema_name,
        expected_version=expected_version,
        path=path,
    )


def schema_version_file_blocker(
    path: str | Path,
    *,
    schema_name: str,
    expected_version: int = CURRENT_SCHEMA_VERSION,
) -> str | None:
    try:
        data = load_json_object(path, schema_name=schema_name)
        require_schema_version(
            data,
            schema_name=schema_name,
            expected_version=expected_version,
            path=path,
        )
    except SchemaVersionError as exc:
        return str(exc)
    return None
