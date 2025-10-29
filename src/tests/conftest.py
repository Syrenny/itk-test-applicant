import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from testcontainers.postgres import PostgresContainer

from src.api._context import RequestContext
from src.api.wallets import router
from src.config import secrets
from src.db.session import session_manager

from .utils import open_connection, open_session


@pytest_asyncio.fixture(scope="session")
async def postgres():
    loop = asyncio.get_event_loop()
    container = await loop.run_in_executor(
        None, lambda: PostgresContainer("postgres:15").start()
    )
    yield container
    await loop.run_in_executor(None, container.stop)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db(postgres) -> AsyncIterator[PostgresContainer]:
    print("Fixture started")

    secrets.postgres_user = SecretStr(postgres.username)
    secrets.postgres_password = SecretStr(postgres.password)
    secrets.postgres_db = SecretStr(postgres.dbname)
    secrets.postgres_port = SecretStr(postgres.get_exposed_port(postgres.port))

    print(f"Connecting to test DB: {secrets.sqlalchemy_url}")

    await session_manager.init_db(run_migrations=True)

    yield


async def is_db_empty(conn: AsyncConnection) -> bool:
    def sync_inspect(connection):
        inspector = inspect(connection)
        tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
        counts = []
        for table in tables:
            result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
            counts.append(result.scalar_one())
        return counts

    counts = await conn.run_sync(sync_inspect)
    return all(c == 0 for c in counts)


# pattern: https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
@pytest_asyncio.fixture(scope="function")
async def isolated_session() -> AsyncIterator[AsyncSession]:
    async with open_connection() as conn:
        assert await is_db_empty(conn) is True
        async with open_session(conn) as session:
            yield session


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI app instance for testing with the wallets router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Provide httpx AsyncClient with injected RequestContext session."""
    async with open_connection() as conn:
        async def override_ctx():
            async with open_session(conn) as session:
                return RequestContext(session=session)

        app.dependency_overrides[RequestContext] = override_ctx

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac
