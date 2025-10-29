from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class OperationType(str, enum.Enum):
    deposit = "DEPOSIT"
    withdraw = "WITHDRAW"


class Base(DeclarativeBase):
    __abstract__ = True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={getattr(self, 'id', None)}>"


class DBOperation(Base):
    __tablename__ = "operations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    op_type: Mapped[OperationType] = mapped_column(
        Enum(OperationType, name="operation_type_enum", native_enum=False),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False
    )


class DBWallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    operations: Mapped[list["DBOperation"]] = relationship(
        "DBOperation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
