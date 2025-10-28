from uuid import UUID

from pydantic import BaseModel

from src.db.models import DBOperation, OperationType


class Operation(BaseModel):
    id: UUID
    wallet_id: UUID
    type: OperationType
    amount: int

    @classmethod
    def from_db(cls, db_op: DBOperation) -> "Operation":
        return cls(
            id=db_op.id, wallet_id=db_op.wallet_id, type=db_op.type, amount=db_op.amount
        )


class Wallet(BaseModel):
    id: UUID
    operations: list[Operation]
