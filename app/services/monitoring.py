import asyncio
import socket
import time
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class TargetSnapshot:
    id: int
    kind: str
    url: str | None
    host: str | None
    port: int | None
    timeout_seconds: float
    interval_seconds: int


@dataclass(frozen=True)
class CheckOutcome:
    status: bool
    latency_ms: float | None = None
    status_code: int | None = None
    error: str | None = None


def _error_message(error: Exception) -> str:
    message = str(error).strip()
    return message or error.__class__.__name__


async def _check_http(target: TargetSnapshot) -> CheckOutcome:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            timeout=target.timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "NetPilot/1.0"},
        ) as client:
            response = await client.get(target.url or "")
        latency = round((time.perf_counter() - started) * 1000, 2)
        is_up = 200 <= response.status_code < 400
        return CheckOutcome(
            status=is_up,
            latency_ms=latency,
            status_code=response.status_code,
            error=None if is_up else f"HTTP {response.status_code}",
        )
    except (httpx.HTTPError, ValueError) as error:
        return CheckOutcome(
            status=False,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            error=_error_message(error),
        )


async def _check_tcp(target: TargetSnapshot) -> CheckOutcome:
    started = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(target.host, target.port),
            timeout=target.timeout_seconds,
        )
        del reader
        writer.close()
        await writer.wait_closed()
        return CheckOutcome(
            status=True,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )
    except (OSError, asyncio.TimeoutError, socket.gaierror) as error:
        return CheckOutcome(
            status=False,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            error=_error_message(error),
        )


async def _check_udp(target: TargetSnapshot) -> CheckOutcome:
    """Check that the OS can create a UDP route to the endpoint.

    UDP has no handshake like TCP. A successful result confirms local socket
    setup and routing, but does not prove that the remote service answered.
    """
    started = time.perf_counter()
    transport = None
    try:
        loop = asyncio.get_running_loop()
        transport, _ = await asyncio.wait_for(
            loop.create_datagram_endpoint(
                asyncio.DatagramProtocol,
                remote_addr=(target.host, target.port),
            ),
            timeout=target.timeout_seconds,
        )
        return CheckOutcome(
            status=True,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )
    except (OSError, asyncio.TimeoutError, socket.gaierror) as error:
        return CheckOutcome(
            status=False,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            error=_error_message(error),
        )
    finally:
        if transport is not None:
            transport.close()


async def check_target(target: TargetSnapshot) -> CheckOutcome:
    if target.kind == "http":
        return await _check_http(target)
    if target.kind == "tcp":
        return await _check_tcp(target)
    if target.kind == "udp":
        return await _check_udp(target)
    return CheckOutcome(status=False, error=f"Неизвестный тип проверки: {target.kind}")

