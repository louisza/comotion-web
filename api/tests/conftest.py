"""Shared test fixtures for the Comotion API tests."""
import pytest_asyncio
from contextlib import asynccontextmanager
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.db import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client():
    """Provide a test client backed by an in-memory SQLite database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    @asynccontextmanager
    async def test_lifespan(_application):
        yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = test_lifespan

    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")

    app.router.lifespan_context = original_lifespan
    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
