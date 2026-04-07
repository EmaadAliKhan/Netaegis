from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def _load_env() -> None:
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env", override=False)


def _build_db_url() -> str:
    _load_env()
    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DB")
    port = os.getenv("MYSQL_PORT", "3306")

    missing = [
        key
        for key, value in {
            "MYSQL_HOST": host,
            "MYSQL_USER": user,
            "MYSQL_PASSWORD": password,
            "MYSQL_DB": database,
        }.items()
        if not value
    ]
    if missing:
        missing_keys = ", ".join(missing)
        raise RuntimeError(f"Missing required database environment variables: {missing_keys}")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


def _get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(
            _build_db_url(),
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            future=True,
        )
    return _ENGINE


def get_db_session() -> Session:
    """
    Return a SQLAlchemy session backed by a pooled MySQL engine.

        with get_db_session() as session:
            ...
    """
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(
            bind=_get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )
    return _SESSION_FACTORY()
