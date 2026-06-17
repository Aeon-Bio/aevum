from __future__ import annotations

import os
from urllib.parse import urlparse

from zeroconf import Zeroconf

from aevum_ot2.core.models import RobotDiscoveryResult

DEFAULT_ROBOT_SERVICE_NAME = "aevum"
DEFAULT_SERVICE_TYPE = "_http._tcp.local."
ROBOT_URL_ENV = "AEVUM_OT2_ROBOT_URL"


def normalize_robot_url(robot_url: str) -> str:
    """Return a robot-server URL with scheme and without a trailing slash."""

    candidate = robot_url.strip()
    if not candidate:
        raise ValueError("robot URL is empty")
    if "://" not in candidate:
        candidate = f"http://{candidate}"

    parsed = urlparse(candidate)
    if not parsed.hostname:
        raise ValueError(f"robot URL has no hostname: {robot_url}")
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported robot URL scheme: {parsed.scheme}")

    return candidate.rstrip("/")


def resolve_robot(
    robot_url: str | None = None,
    *,
    service_name: str = DEFAULT_ROBOT_SERVICE_NAME,
    timeout_seconds: float = 5.0,
) -> RobotDiscoveryResult:
    """Resolve the robot URL from explicit input, environment, or mDNS."""

    if robot_url:
        return RobotDiscoveryResult(
            robot_url=normalize_robot_url(robot_url),
            source="argument",
        )

    env_robot_url = os.environ.get(ROBOT_URL_ENV)
    if env_robot_url:
        return RobotDiscoveryResult(
            robot_url=normalize_robot_url(env_robot_url),
            source="environment",
        )

    return resolve_robot_mdns(service_name=service_name, timeout_seconds=timeout_seconds)


def resolve_robot_mdns(
    *,
    service_name: str = DEFAULT_ROBOT_SERVICE_NAME,
    service_type: str = DEFAULT_SERVICE_TYPE,
    timeout_seconds: float = 5.0,
) -> RobotDiscoveryResult:
    """Resolve an OT-2 HTTP service advertised over mDNS."""

    normalized_service_type = _normalize_service_type(service_type)
    instance_name = f"{service_name}.{normalized_service_type}"

    with Zeroconf() as zeroconf:
        service_info = zeroconf.get_service_info(
            normalized_service_type,
            instance_name,
            timeout=int(timeout_seconds * 1000),
        )

    if service_info is None:
        raise RuntimeError(
            f"could not resolve mDNS service {instance_name!r} within {timeout_seconds:g}s"
        )

    addresses = service_info.parsed_addresses()
    server = service_info.server.rstrip(".") if service_info.server else None
    host = server or (addresses[0] if addresses else None)
    if host is None:
        raise RuntimeError(f"mDNS service {instance_name!r} did not include a host address")

    properties = {
        _decode_txt_value(key): _decode_txt_value(value)
        for key, value in service_info.properties.items()
    }

    return RobotDiscoveryResult(
        robot_url=f"http://{host}:{service_info.port}",
        source="mdns",
        service_name=service_name,
        service_type=normalized_service_type,
        server=server,
        addresses=addresses,
        port=service_info.port,
        properties=properties,
    )


def _normalize_service_type(service_type: str) -> str:
    normalized = service_type.strip()
    if not normalized.endswith("."):
        normalized += "."
    return normalized


def _decode_txt_value(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.decode("utf-8", errors="replace")
