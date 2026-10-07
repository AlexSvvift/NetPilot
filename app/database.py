from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


def _prepare_sqlite_path(database_url: str) -> None:
    """Create the parent directory for a local SQLite database."""
    if not database_url.startswith("sqlite:///") or ":memory:" in database_url:
        return

    database_path = database_url.removeprefix("sqlite:///")
    Path(database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def create_database(database_url: str) -> tuple[Engine, sessionmaker]:
    _prepare_sqlite_path(database_url)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return engine, session_factory


def initialize_database(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)

