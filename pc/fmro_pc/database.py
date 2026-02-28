from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

DEFAULT_DB_NAME = "fmro_pc.db"


def resolve_db_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path)
    root = Path(__file__).resolve().parents[1]
    return root / "data" / DEFAULT_DB_NAME


@lru_cache(maxsize=8)
def get_engine(path: str | Path | None = None):
    db_path = resolve_db_path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )


def init_db(path: str | Path | None = None) -> None:
    # Ensure models are imported before metadata creation.
    from fmro_pc import models  # noqa: F401

    engine = get_engine(path)
    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope(path: str | Path | None = None):
    engine = get_engine(path)
    with Session(engine) as session:
        yield session
