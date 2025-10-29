from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dao import DaoOperation
from src.db.models import OperationType
from src.exceptions.wallets import WalletNotFoundError
from src.models.dto import Operation


class OperationService:
    @classmethod
    async def add_operation(
        cls, session: AsyncSession, wallet_id: UUID, op_type: OperationType, amount: int
    ) -> Operation:
        try:
            db_op = await DaoOperation.add_operation(
                session=session, wallet_id=wallet_id, op_type=op_type, amount=amount
            )
        except IntegrityError as e:
            raise WalletNotFoundError(wallet_id=wallet_id) from e

        return Operation.from_db(db_op)
