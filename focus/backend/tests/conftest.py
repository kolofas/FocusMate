# focus/backend/tests/conftest.py
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from focus.backend.app import app
from focus.backend.database.models import Base
from focus.backend.database.core import get_db
from focus.backend.settings import settings


TEST_SCHEMA = "test_schema"


@pytest.fixture(scope="session")
def engine():
    url = settings.database_url
    eng = create_engine(url, future=True)

    # все DDL — на одном соединении с выставленным search_path
    with eng.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{TEST_SCHEMA}"'))
        conn.execute(text(f'SET search_path TO "{TEST_SCHEMA}"'))
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)

    yield eng

    # чистим схему после сессии
    with eng.begin() as conn:
        conn.execute(text("SET search_path TO public"))
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))


@pytest.fixture
def db_session(engine):
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    sess = SessionLocal()
    sess.execute(text(f'SET search_path TO "{TEST_SCHEMA}"'))
    try:
        yield sess
    finally:
        sess.rollback()
        sess.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
