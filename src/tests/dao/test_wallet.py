import asyncio
from uuid import uuid4

import pytest

from src.db.dao import DaoOperation, DaoWallet
from src.db.models import OperationType
from src.tests.utils import open_connection, open_session


@pytest.mark.asyncio(loop_scope="session")
async def test_create_wallet_initial_balance(isolated_session):
    """Wallet should be created with the specified initial balance."""

    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=100)
    assert wallet is not None
    assert wallet.balance == 100


@pytest.mark.asyncio(loop_scope="session")
async def test_get_wallet_existing(isolated_session):
    """Should return the wallet if it exists."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=50)
    fetched = await DaoWallet.get_wallet(session=isolated_session, wallet_id=wallet.id)
    assert fetched is not None
    assert fetched.id == wallet.id
    assert fetched.balance == 50


@pytest.mark.asyncio(loop_scope="session")
async def test_get_wallet_nonexistent(isolated_session):
    """Should return None if wallet does not exist."""
    fetched = await DaoWallet.get_wallet(session=isolated_session, wallet_id=uuid4())
    assert fetched is None


@pytest.mark.asyncio(loop_scope="session")
async def test_add_to_balance_positive_amount(isolated_session):
    """Balance should increase correctly with positive amount."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=0)
    updated = await DaoWallet.add_to_balance(
        session=isolated_session, wallet_id=wallet.id, amount=200
    )
    assert updated.balance == 200


@pytest.mark.asyncio(loop_scope="session")
async def test_add_to_balance_negative_amount(isolated_session):
    """Balance should decrease correctly with negative amount."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=500)
    updated = await DaoWallet.add_to_balance(
        session=isolated_session, wallet_id=wallet.id, amount=-150
    )
    assert updated.balance == 350


@pytest.mark.asyncio(loop_scope="session")
async def test_add_to_balance_zero_amount(isolated_session):
    """Balance should remain the same if amount is zero."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=100)
    updated = await DaoWallet.add_to_balance(
        session=isolated_session, wallet_id=wallet.id, amount=0
    )
    assert updated.balance == 100


@pytest.mark.asyncio(loop_scope="session")
async def test_add_to_balance_nonexistent_wallet(isolated_session):
    """Should return None when adding to a non-existent wallet."""
    updated = await DaoWallet.add_to_balance(
        session=isolated_session, wallet_id=uuid4(), amount=100
    )
    assert updated is None


@pytest.mark.asyncio(loop_scope="session")
async def test_add_operation_links_wallet(isolated_session):
    """Operation should be correctly linked to the wallet."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=100)
    operation = await DaoOperation.add_operation(
        session=isolated_session,
        wallet_id=wallet.id,
        op_type=OperationType.deposit,
        amount=50,
    )
    assert operation.wallet_id == wallet.id
    # Ensure wallet balance is not changed automatically unless add_to_balance is called
    fetched_wallet = await DaoWallet.get_wallet(
        session=isolated_session, wallet_id=wallet.id
    )
    assert fetched_wallet.balance == 100


@pytest.mark.asyncio(loop_scope="session")
async def test_multiple_operations_update_balance(isolated_session):
    """Multiple sequential operations should result in correct balance."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=100)
    await DaoWallet.add_to_balance(
        session=isolated_session, wallet_id=wallet.id, amount=50
    )
    await DaoWallet.add_to_balance(
        session=isolated_session, wallet_id=wallet.id, amount=-30
    )
    await DaoWallet.add_to_balance(
        session=isolated_session, wallet_id=wallet.id, amount=20
    )
    fetched = await DaoWallet.get_wallet(session=isolated_session, wallet_id=wallet.id)
    assert fetched.balance == 140  # 100 + 50 - 30 + 20


@pytest.mark.asyncio(loop_scope="session")
async def test_race_condition_add_to_balance(isolated_session):
    """Concurrent balance updates should be atomic and result in correct final balance."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=0)

    async def increment(amount: int):
        await DaoWallet.add_to_balance(
            session=isolated_session, wallet_id=wallet.id, amount=amount
        )

    # Launch multiple concurrent increments
    increments = [increment(10) for _ in range(10)]
    await asyncio.gather(*increments)

    fetched = await DaoWallet.get_wallet(session=isolated_session, wallet_id=wallet.id)
    assert fetched.balance == 100  # 10 increments of 10


@pytest.mark.asyncio(loop_scope="session")
async def test_create_wallet_negative_balance(isolated_session):
    """Wallet can be created with a negative balance if allowed."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=-50)
    assert wallet.balance == -50


@pytest.mark.asyncio(loop_scope="session")
async def test_add_operation_zero_amount(isolated_session):
    """Adding an operation with zero amount should succeed but not affect balance."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=100)
    op = await DaoOperation.add_operation(
        session=isolated_session,
        wallet_id=wallet.id,
        op_type=OperationType.deposit,
        amount=0,
    )
    assert op.amount == 0
    fetched = await DaoWallet.get_wallet(session=isolated_session, wallet_id=wallet.id)
    assert fetched.balance == 100


@pytest.mark.asyncio(loop_scope="session")
async def test_add_multiple_operations_without_balance_update(isolated_session):
    """Multiple operations do not change balance unless add_to_balance is called."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=200)
    for amount in [10, -20, 30]:
        await DaoOperation.add_operation(
            session=isolated_session,
            wallet_id=wallet.id,
            op_type=OperationType.deposit,
            amount=amount,
        )
    fetched = await DaoWallet.get_wallet(session=isolated_session, wallet_id=wallet.id)
    assert fetched.balance == 200  # balance unchanged


@pytest.mark.asyncio(loop_scope="session")
async def test_large_amount_operations(isolated_session):
    """Handles large increments and decrements correctly."""
    wallet = await DaoWallet.create_wallet(session=isolated_session, balance=1_000_000)
    await DaoWallet.add_to_balance(
        session=isolated_session, wallet_id=wallet.id, amount=2_000_000
    )
    await DaoWallet.add_to_balance(
        session=isolated_session, wallet_id=wallet.id, amount=-500_000
    )
    fetched = await DaoWallet.get_wallet(session=isolated_session, wallet_id=wallet.id)
    assert fetched.balance == 2_500_000


@pytest.mark.asyncio(loop_scope="session")
async def test_concurrent_operations_with_operations():
    """Concurrent operations added via DaoOperation do not automatically affect balance."""
    async with open_connection() as conn:
        async with open_session(conn) as session:
            wallet = await DaoWallet.create_wallet(session=session, balance=0)

        async def add_op(amount: int):
            async with open_session(conn) as session:
                await DaoOperation.add_operation(
                    session=session,
                    wallet_id=wallet.id,
                    op_type=OperationType.deposit,
                    amount=amount,
                )

        tasks = [add_op(10) for _ in range(10)]
        await asyncio.gather(*tasks)

        async with open_session(conn) as session:
            fetched = await DaoWallet.get_wallet(session=session, wallet_id=wallet.id)
        assert fetched.balance == 0  # balance unchanged
