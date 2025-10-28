from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db


class RequestContext:
    def __init__(
        self,
        session: AsyncSession = Depends(get_db),
    ):
        self.session = session
