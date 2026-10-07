import asyncio
import logging
import time

from app.repository import Repository
from app.services.monitoring import CheckOutcome, check_target

logger = logging.getLogger(__name__)


async def monitoring_loop(
    repository: Repository,
    tick_seconds: int,
    stop_event: asyncio.Event,
) -> None:
    """Run due checks without blocking FastAPI request handling."""
    last_runs: dict[int, float] = {}

    while not stop_event.is_set():
        now = time.monotonic()
        snapshots = await asyncio.to_thread(repository.list_enabled_snapshots)
        due = [
            snapshot
            for snapshot in snapshots
            if now - last_runs.get(snapshot.id, 0) >= snapshot.interval_seconds
        ]

        if due:
            outcomes = await asyncio.gather(
                *(check_target(snapshot) for snapshot in due),
                return_exceptions=True,
            )
            for snapshot, outcome in zip(due, outcomes, strict=True):
                last_runs[snapshot.id] = now
                if isinstance(outcome, Exception):
                    outcome = CheckOutcome(status=False, error=str(outcome))
                await asyncio.to_thread(repository.record_check, snapshot.id, outcome)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=tick_seconds)
        except asyncio.TimeoutError:
            continue
