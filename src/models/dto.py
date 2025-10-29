from uuid import UUID

from pydantic import BaseModel

from src.db.models import DBOperation, OperationType


class Operation(BaseModel):
    id: UUID
    wallet_id: UUID
    op_type: OperationType
    amount: int

    @classmethod
    def from_db(cls, db_op: DBOperation) -> "Operation":
        return cls(
            id=db_op.id,
            wallet_id=db_op.wallet_id,
            op_type=db_op.op_type,
            amount=db_op.amount,
        )


class Wallet(BaseModel):
    id: UUID
    operations: list[Operation]
