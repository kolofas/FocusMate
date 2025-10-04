# tests/conftest.py
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from focus.backend.app import app
from focus.backend.database.models import Base
from focus.backend.database.core import get_db  # твой Depends-провайдер


@pytest.fixture(scope="session")
def engine():
    # один общий in-memory для всех соединений
    eng = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    # создаём таблицы на этом же engine
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture
def db_session(engine):
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    sess = SessionLocal()
    try:
        yield sess
    finally:
        sess.rollback()
        sess.close()


@pytest.fixture
def client(db_session):
    # подменяем зависимость get_db, чтобы app использовало нашу сессию
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
