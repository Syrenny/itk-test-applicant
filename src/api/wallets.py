from uuid import UUID

from fastapi import APIRouter, Depends

from src.db.models import OperationType
from src.services.wallets import WalletService

from ._context import RequestContext

router = APIRouter()


@router.post(
    "/wallets",
    tags=["Wallets"],
    summary="Create new wallet",
)
async def create_wallet(
    balance: int = 0,
    ctx: RequestContext = Depends(),
) -> UUID:
    return await WalletService.create_wallet(session=ctx.session, balance=balance)


@router.post(
    "/wallets/{wallet_id}/operation",
    tags=["Wallets"],
    summary="Add new operation to wallet",
)
async def add_operation(
    wallet_id: UUID,
    op_type: OperationType,
    amount: int = 1000,
    ctx: RequestContext = Depends(),
) -> None:
    await WalletService.process_operation(
        session=ctx.session, wallet_id=wallet_id, op_type=op_type, amount=amount
    )


@router.get(
    "/wallets/{wallet_id}",
    tags=["Wallets"],
    summary="Get the balance of wallet",
)
async def get_balance(
    wallet_id: UUID,
    ctx: RequestContext = Depends(),
) -> None:
    balance = await WalletService.get_balance(session=ctx.session, wallet_id=wallet_id)

    return balance
