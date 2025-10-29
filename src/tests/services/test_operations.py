import asyncio
from uuid import uuid4

import pytest

from src.db.dao import DaoOperation, DaoWallet
from src.db.models import OperationType
from src.exceptions.wallets import WalletNotFoundError
from src.models.dto import Operation
from src.services.operations import OperationService
from src.tests.utils import open_connection, open_session


@pytest.mark.asyncio(loop_scope="session")
async def test_add_operation_success():
    """OperationService.add_operation creates a DB operation successfully."""
    async with open_connection() as conn:
        async with open_session(conn) as session:
            wallet = await DaoWallet.create_wallet(session=session, balance=0)

            op = await OperationService.add_operation(
                session=session,
                wallet_id=wallet.id,
                op_type=OperationType.deposit,
                amount=100,
            )

        assert isinstance(op, Operation)
        assert op.wallet_id == wallet.id
        assert op.amount == 100
        assert op.op_type == OperationType.deposit

        async with open_session(conn) as session:
            db_op = await DaoOperation.get_operation(session=session, op_id=op.id)
        assert db_op is not None
        assert db_op.amount == 100


@pytest.mark.asyncio(loop_scope="session")
async def test_add_operation_wallet_not_found(isolated_session):
    """Raises WalletNotFoundError if wallet does not exist."""
    fake_wallet_id = uuid4()

    with pytest.raises(WalletNotFoundError) as exc_info:
        await OperationService.add_operation(
            session=isolated_session,
            wallet_id=fake_wallet_id,
            op_type=OperationType.deposit,
            amount=50,
        )
    assert str(fake_wallet_id) in str(exc_info.value)


@pytest.mark.asyncio(loop_scope="session")
async def test_concurrent_add_operations():
    """Multiple concurrent operations do not break consistency."""
    async with open_connection() as conn:
        async with open_session(conn) as session:
            wallet = await DaoWallet.create_wallet(session=session, balance=0)

        async def add_op(amount: int):
            async with open_session(conn) as session:
                return await OperationService.add_operation(
                    session=session,
                    wallet_id=wallet.id,
                    op_type=OperationType.deposit,
                    amount=amount,
                )

        tasks = [add_op(10) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert all(isinstance(r, Operation) for r in results)

        async with open_session(conn) as session:
            fetched_wallet = await DaoWallet.get_wallet(
                session=session, wallet_id=wallet.id
            )
        assert fetched_wallet.balance == 0
        assert len(fetched_wallet.operations) == 10
        assert sum(op.amount for op in fetched_wallet.operations) == 100
