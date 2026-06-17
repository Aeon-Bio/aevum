from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from aevum_ot2.core.models import EndpointResult, RobotStatus


class Ot2Client:
    """Narrow client for the Opentrons robot server."""

    def __init__(
        self,
        robot_url: str,
        *,
        opentrons_version: str = "*",
        timeout_seconds: float = 5.0,
    ) -> None:
        self.robot_url = robot_url.rstrip("/") + "/"
        self.opentrons_version = opentrons_version
        self.timeout_seconds = timeout_seconds

    def get_json(self, path: str) -> EndpointResult:
        result = self._get(path)
        if not result.ok or result.text is None:
            return result

        try:
            result.data = json.loads(result.text)
            result.text = None
        except json.JSONDecodeError as exc:
            result.ok = False
            result.error = f"invalid JSON response: {exc}"

        return result

    def get_text(self, path: str) -> EndpointResult:
        return self._get(path)

    def post_json(
        self,
        path: str,
        body: dict[str, Any] | list[Any] | None = None,
    ) -> EndpointResult:
        return self._request_json("POST", path, body)

    def delete_json(self, path: str) -> EndpointResult:
        return self._request_json("DELETE", path)

    def status(self, *, include_openapi: bool = False) -> RobotStatus:
        health = self.get_json("/health")
        pipettes = self.get_json("/pipettes")
        openapi = self.get_json("/openapi.json") if include_openapi else None

        if openapi is not None and not openapi.ok:
            openapi = self.get_text("/openapi")

        return RobotStatus(
            robot_url=self.robot_url.rstrip("/"),
            checked_at=datetime.now(),
            health=health,
            pipettes=pipettes,
            openapi=openapi,
        )

    def _get(self, path: str) -> EndpointResult:
        return self._request_text("GET", path)

    def _request_text(self, method: str, path: str) -> EndpointResult:
        normalized_path = "/" + path.lstrip("/")
        url = urljoin(self.robot_url, normalized_path.lstrip("/"))
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "Opentrons-Version": self.opentrons_version,
            },
            method=method,
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
                return EndpointResult(
                    path=normalized_path,
                    ok=200 <= response.status < 300,
                    status_code=response.status,
                    text=body,
                )
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return EndpointResult(
                path=normalized_path,
                ok=False,
                status_code=exc.code,
                text=body,
                error=str(exc),
            )
        except (TimeoutError, URLError, OSError) as exc:
            return EndpointResult(path=normalized_path, ok=False, error=str(exc))

    def _request_json(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | list[Any] | None = None,
    ) -> EndpointResult:
        normalized_path = "/" + path.lstrip("/")
        url = urljoin(self.robot_url, normalized_path.lstrip("/"))
        request_body = json.dumps(body).encode("utf-8")
        request = Request(
            url,
            data=request_body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Opentrons-Version": self.opentrons_version,
            },
            method=method,
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                text = response.read().decode("utf-8", errors="replace")
                result = EndpointResult(
                    path=normalized_path,
                    ok=200 <= response.status < 300,
                    status_code=response.status,
                    text=text,
                )
        except HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            result = EndpointResult(
                path=normalized_path,
                ok=False,
                status_code=exc.code,
                text=text,
                error=str(exc),
            )
        except (TimeoutError, URLError, OSError) as exc:
            return EndpointResult(path=normalized_path, ok=False, error=str(exc))

        if result.text:
            try:
                result.data = json.loads(result.text)
                result.text = None
            except json.JSONDecodeError as exc:
                result.ok = False
                result.error = f"invalid JSON response: {exc}"

        return result


def summarize_endpoint_data(
    data: dict[str, Any] | list[Any] | None,
) -> dict[str, Any] | list[Any] | None:
    if isinstance(data, dict):
        return {key: data[key] for key in sorted(data)[:20]}
    return data


def fetch_robot_status(robot_url: str, *, timeout_seconds: float = 5.0) -> RobotStatus:
    return Ot2Client(robot_url, timeout_seconds=timeout_seconds).status()
