from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dao import DaoWallet
from src.db.models import OperationType
from src.exceptions.wallets import WalletNotFoundError
from src.models.dto import Operation
from src.services.operations import OperationService


class WalletService:
    @classmethod
    async def get_balance(cls, session: AsyncSession, wallet_id: UUID) -> int:
        db_wallet = await DaoWallet.get_wallet(session=session, wallet_id=wallet_id)

        if db_wallet is None:
            raise WalletNotFoundError(wallet_id=wallet_id)

        return db_wallet.balance

    @classmethod
    async def add_to_balance(
        cls, session: AsyncSession, wallet_id: UUID, amount: int
    ) -> None:
        db_wallet = await DaoWallet.add_to_balance(
            session=session, wallet_id=wallet_id, amount=amount
        )

        if db_wallet is None:
            raise WalletNotFoundError(wallet_id=wallet_id)

    @classmethod
    async def process_operation(
        cls, session: AsyncSession, wallet_id: UUID, op_type: OperationType, amount: int
    ) -> Operation:
        await OperationService.add_operation(
            session=session, wallet_id=wallet_id, op_type=op_type, amount=amount
        )

        if op_type == OperationType.withdraw:
            amount = -amount

        await cls.add_to_balance(session=session, wallet_id=wallet_id, amount=amount)
