import asyncio
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncConnection

from src.services.wallets import WalletService
from src.tests.utils import open_session


@pytest.mark.asyncio(loop_scope="session")
async def test_create_wallet(client: AsyncClient, db_conn: AsyncConnection):
    response = await client.post("/wallets", params={"balance": 500})
    assert response.status_code == 200

    wallet_id = UUID(response.json())
    async with open_session(db_conn) as session:
        balance = await WalletService.get_balance(session=session, wallet_id=wallet_id)
    assert balance == 500


@pytest.mark.asyncio(loop_scope="session")
async def test_add_operation(client: AsyncClient, db_conn: AsyncConnection):
    response = await client.post("/wallets", params={"balance": 100})
    wallet_id = UUID(response.json())

    op_data = {"op_type": "DEPOSIT", "amount": 200}
    response = await client.post(f"/wallets/{wallet_id}/operation", params=op_data)
    assert response.status_code == 200

    async with open_session(db_conn) as session:
        balance = await WalletService.get_balance(session=session, wallet_id=wallet_id)
    assert balance == 300


@pytest.mark.asyncio(loop_scope="session")
async def test_concurrent_operations(client: AsyncClient, db_conn: AsyncConnection):
    response = await client.post("/wallets", params={"balance": 0})
    wallet_id = UUID(response.json())

    async def add_op(amount: int):
        op_data = {"op_type": "DEPOSIT", "amount": amount}
        await client.post(f"/wallets/{wallet_id}/operation", params=op_data)

    tasks = [add_op(100) for _ in range(10)]
    await asyncio.gather(*tasks)

    async with open_session(db_conn) as session:
        balance = await WalletService.get_balance(session=session, wallet_id=wallet_id)

    assert balance == 1000


@pytest.mark.asyncio(loop_scope="session")
async def test_withdrawal_operation(client: AsyncClient, db_conn: AsyncConnection):
    response = await client.post("/wallets", params={"balance": 500})
    wallet_id = UUID(response.json())

    op_data = {"op_type": "WITHDRAW", "amount": 200}
    await client.post(f"/wallets/{wallet_id}/operation", params=op_data)

    async with open_session(db_conn) as session:
        balance = await WalletService.get_balance(session=session, wallet_id=wallet_id)

    assert balance == 300
