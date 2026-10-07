from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create an isolated application with a temporary SQLite database."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("API_KEY", "test-key")
    get_settings.cache_clear()

    application = create_app()
    with TestClient(application) as test_client:
        yield test_client

    get_settings.cache_clear()
