import asyncio
from uuid import UUID

import pytest
from httpx import AsyncClient

from src.db.session import session_manager
from src.services.wallets import WalletService


@pytest.mark.asyncio(loop_scope="session")
async def test_create_wallet(client: AsyncClient):
    # Создание кошелька через API
    response = await client.post("/wallets", json={"balance": 500})
    assert response.status_code == 200

    wallet_id = UUID(response.json())
    # Проверяем баланс через сервис напрямую
    async with session_manager.session() as session:
        balance = await WalletService.get_balance(session=session, wallet_id=wallet_id)
    assert balance == 500


@pytest.mark.asyncio(loop_scope="session")
async def test_add_operation(client: AsyncClient):
    # Создаем кошелек
    response = await client.post("/wallets", json={"balance": 100})
    wallet_id = UUID(response.json())

    # Добавляем операцию
    op_data = {"op_type": "deposit", "amount": 200}
    response = await client.post(f"/wallets/{wallet_id}/operation", json=op_data)
    assert response.status_code == 200

    # Проверяем баланс
    async with session_manager.session() as session:
        balance = await WalletService.get_balance(session=session, wallet_id=wallet_id)
    assert balance == 300


@pytest.mark.asyncio(loop_scope="session")
async def test_concurrent_operations(client: AsyncClient):
    # Создаем кошелек
    response = await client.post("/wallets", json={"balance": 0})
    wallet_id = UUID(response.json())

    async def add_op(amount: int):
        op_data = {"op_type": "deposit", "amount": amount}
        await client.post(f"/wallets/{wallet_id}/operation", json=op_data)

    # Запускаем несколько операций параллельно
    tasks = [add_op(100) for _ in range(10)]
    await asyncio.gather(*tasks)

    async with session_manager.session() as session:
        balance = await WalletService.get_balance(session=session, wallet_id=wallet_id)

    # Проверяем, что баланс учитывает все операции
    assert balance == 1000


@pytest.mark.asyncio(loop_scope="session")
async def test_withdrawal_operation(client: AsyncClient):
    # Создаем кошелек с балансом
    response = await client.post("/wallets", json={"balance": 500})
    wallet_id = UUID(response.json())

    # Снимаем деньги
    op_data = {"op_type": "withdrawal", "amount": 200}
    await client.post(f"/wallets/{wallet_id}/operation", json=op_data)

    async with session_manager.session() as session:
        balance = await WalletService.get_balance(session=session, wallet_id=wallet_id)

    assert balance == 300
