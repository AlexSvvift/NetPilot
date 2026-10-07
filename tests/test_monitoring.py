import asyncio

import pytest

from app.services.monitoring import TargetSnapshot, check_target


@pytest.mark.asyncio
async def test_tcp_monitoring_detects_local_listener():
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    try:
        result = await check_target(
            TargetSnapshot(
                id=1,
                kind="tcp",
                url=None,
                host="127.0.0.1",
                port=port,
                timeout_seconds=1,
                interval_seconds=60,
            )
        )
    finally:
        server.close()
        await server.wait_closed()

    assert result.status is True
    assert result.error is None
    assert result.latency_ms is not None
