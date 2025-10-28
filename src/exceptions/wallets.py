from uuid import UUID

from src.exceptions.base import AppException


class WalletNotFoundError(AppException):
    def __init__(self, wallet_id: UUID):
        super().__init__(f"Wallet with wallet_id={wallet_id} not found")
