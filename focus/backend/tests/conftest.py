from __future__ import annotations

import uuid

import pytest
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from focus.backend.app import app
from focus.backend.database.models import Base
from focus.backend.database.core import get_db
from focus.backend.settings import settings


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def engine_and_schema():
    """
    Важно: function-scope.
    Каждый тест получает свой schema + свой engine, созданные в том же event loop,
    что и тест (AnyIO), поэтому asyncpg не ругается на "different loop".
    """
    schema = f"test_{uuid.uuid4().hex}"

    engine = create_async_engine(settings.database_url, future=True)

    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        await conn.execute(text(f'SET search_path TO "{schema}"'))
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine, schema
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("SET search_path TO public"))
            await conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await engine.dispose()


@pytest.fixture
async def client(engine_and_schema):
    engine, schema = engine_and_schema

    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    async def _override_get_db():
        async with SessionLocal() as session:
            # выставляем schema для каждого запроса
            await session.execute(text(f'SET search_path TO "{schema}"'))
            yield session
            # безопасность: если роутер не закрыл транзакцию — откатим
            await session.rollback()

    app.dependency_overrides[get_db] = _override_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
