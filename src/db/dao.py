from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.db.models import DBOperation, DBWallet, OperationType
from src.db.wrap import transactional


class DaoOperation:
    @classmethod
    @transactional
    async def add_operation(
        cls, session: AsyncSession, wallet_id: UUID, op_type: OperationType, amount: int
    ) -> DBOperation:
        db_op = DBOperation(
            op_type=op_type,
            amount=amount,
            wallet_id=wallet_id,
        )
        session.add(db_op)

        return db_op

    @classmethod
    @transactional
    async def get_operation(
        cls,
        session: AsyncSession,
        op_id: UUID,
    ) -> DBOperation | None:
        stmt = select(DBOperation).filter(DBOperation.id == op_id)

        result = await session.execute(stmt)

        return result.scalars().first()


class DaoWallet:
    @classmethod
    @transactional
    async def create_wallet(
        cls, session: AsyncSession, balance: int = 0
    ) -> DBWallet | None:
        db_wallet = DBWallet(balance=balance)
        session.add(db_wallet)

        return db_wallet

    @classmethod
    @transactional
    async def get_wallet(
        cls,
        session: AsyncSession,
        wallet_id: UUID,
    ) -> DBWallet | None:
        stmt = (
            select(DBWallet)
            .filter(DBWallet.id == wallet_id)
            .options(
                selectinload(DBWallet.operations),
            )
        )

        result = await session.execute(stmt)

        return result.scalars().first()

    @classmethod
    @transactional
    async def add_to_balance(
        cls, session: AsyncSession, wallet_id: UUID, amount: int
    ) -> DBWallet | None:
        stmt = (
            update(DBWallet)
            .where(DBWallet.id == wallet_id)
            .values(balance=DBWallet.balance + amount)
            .returning(DBWallet)
        )
        result = await session.execute(stmt)

        return result.scalars().first()
