from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from src.db.session import session_manager


@asynccontextmanager
async def open_connection() -> AsyncIterator[AsyncConnection]:
    async with session_manager.engine.connect() as conn:
        outer_trans = await conn.begin()
        try:
            yield conn
        finally:
            await outer_trans.rollback()


@asynccontextmanager
async def open_session(conn: AsyncConnection) -> AsyncIterator[AsyncSession]:
    async with session_manager.sessionmaker(bind=conn) as session:
        try:
            yield session
        finally:
            await session.close()
