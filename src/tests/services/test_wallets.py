import asyncio
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dao import DaoWallet
from src.db.models import OperationType
from src.exceptions.wallets import WalletNotFoundError
from src.services.wallets import WalletService
from src.tests.utils import open_connection, open_session


@pytest.mark.asyncio(loop_scope="session")
async def test_get_balance_returns_correct_value(isolated_session: AsyncSession):
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=100)

    balance = await WalletService.get_balance(
        session=isolated_session, wallet_id=wallet.id
    )
    assert balance == 100


@pytest.mark.asyncio(loop_scope="session")
async def test_get_balance_raises_if_wallet_missing(isolated_session: AsyncSession):
    fake_id = uuid4()
    with pytest.raises(WalletNotFoundError) as exc:
        await WalletService.get_balance(session=isolated_session, wallet_id=fake_id)
    assert str(fake_id) in str(exc.value)


@pytest.mark.asyncio(loop_scope="session")
async def test_add_to_balance_increases_balance(isolated_session: AsyncSession):
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=50)

    new_balance = await WalletService.add_to_balance(
        session=isolated_session, wallet_id=wallet.id, amount=25
    )
    assert new_balance == 75

    # check DB reflects it
    db_wallet = await DaoWallet.get_wallet(
        session=isolated_session, wallet_id=wallet.id
    )
    assert db_wallet.balance == 75


@pytest.mark.asyncio(loop_scope="session")
async def test_add_to_balance_raises_if_wallet_missing(isolated_session: AsyncSession):
    fake_id = uuid4()
    with pytest.raises(WalletNotFoundError):
        await WalletService.add_to_balance(
            session=isolated_session, wallet_id=fake_id, amount=10
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_process_operation_deposit_and_withdraw(isolated_session: AsyncSession):
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=100)

    # Deposit 50
    await WalletService.process_operation(
        isolated_session, wallet.id, OperationType.deposit, 50
    )
    db_wallet = await DaoWallet.get_wallet(
        session=isolated_session, wallet_id=wallet.id
    )
    assert db_wallet.balance == 150

    # Withdraw 30
    await WalletService.process_operation(
        isolated_session, wallet.id, OperationType.withdraw, 30
    )
    db_wallet = await DaoWallet.get_wallet(
        session=isolated_session, wallet_id=wallet.id
    )
    assert db_wallet.balance == 120
    
    await isolated_session.refresh(db_wallet)

    # Ensure operation is recorded
    ops = db_wallet.operations
    amounts = [op.amount for op in ops]
    assert 50 in amounts and 30 in amounts


@pytest.mark.asyncio(loop_scope="session")
async def test_process_operation_raises_if_wallet_missing(
    isolated_session: AsyncSession,
):
    fake_id = uuid4()
    with pytest.raises(WalletNotFoundError):
        await WalletService.process_operation(
            isolated_session, fake_id, OperationType.deposit, 10
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_concurrent_operations_update_balance_correctly():
    """10 concurrent deposits of 10 should increase balance by 100."""
    async with open_connection() as conn:
        async with open_session(conn) as session:
            wallet = await DaoWallet.create_wallet(session=session, balance=0)

        async def add_deposit(amount: int):
            async with open_session(conn) as session:
                await WalletService.process_operation(
                    session, wallet.id, OperationType.deposit, amount
                )

        tasks = [add_deposit(10) for _ in range(10)]
        await asyncio.gather(*tasks)

        async with open_session(conn) as session:
            db_wallet = await DaoWallet.get_wallet(session=session, wallet_id=wallet.id)
        assert db_wallet.balance == 100
