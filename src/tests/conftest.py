import asyncio
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.postgres import PostgresContainer

from src.config import secrets
from src.db.session import session_manager


@pytest.fixture(scope="session", autouse=True)
def pg_container() -> Iterator[PostgresContainer]:
    print("Fixture started")
    with PostgresContainer("postgres:15", driver="asyncpg") as postgres:
        postgres.start()

        secrets.postgres_user = SecretStr(postgres.username)
        secrets.postgres_password = SecretStr(postgres.password)
        secrets.postgres_db = SecretStr(postgres.dbname)
        secrets.postgres_port = SecretStr(postgres.port)

        print(f"Connecting to test DB: {secrets.sqlalchemy_url}")

        asyncio.run(session_manager.init_db(run_migrations=True))

        yield postgres


@pytest_asyncio.fixture(scope="function")
async def isolated_session() -> AsyncIterator[AsyncSession]:
    async with session_manager.session() as session:
        async with session.begin_nested():
            yield session
