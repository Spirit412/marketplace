from typing import Any
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.datatype import uuid7
from src.models.base import Base, CreatedAtMixin, SoftDeleteMixin, TimestampMixin


class Payment(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "payments"
    __table_args__ = {"schema": "payment", "comment": "Платёж по заказу"}

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ платежа"
    )
    order_id: Mapped[UUID] = mapped_column(
        unique=True,
        index=True,
        comment="Заказ, к которому относится платёж (id из order-service)",
    )
    user_id: Mapped[UUID] = mapped_column(index=True, comment="Плательщик")
    amount: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Сумма платежа, в минорных единицах валюты"
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="RUB", comment="Код валюты (ISO 4217)"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", comment="Статус платежа"
    )
    payment_method: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Способ оплаты"
    )
    gateway: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Платёжный шлюз (stripe/yookassa/mock)"
    )
    gateway_payment_id: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="Идентификатор платежа в системе шлюза"
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        comment="Ключ идемпотентности запроса создания платежа",
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="payment", lazy="selectin"
    )


class Transaction(CreatedAtMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = {
        "schema": "payment",
        "comment": "Операция по платежу (списание, возврат и т.п.) в системе шлюза",
    }

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ операции"
    )
    payment_id: Mapped[UUID] = mapped_column(
        ForeignKey("payment.payments.id", ondelete="CASCADE"),
        nullable=False,
        comment="Платёж (fk на payments.id)",
    )
    transaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Тип операции (capture/refund и т.п.)"
    )
    amount: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Сумма операции, в минорных единицах валюты"
    )
    gateway_transaction_id: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="Идентификатор операции в системе шлюза"
    )
    gateway_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="Дополнительные данные ответа шлюза"
    )

    payment: Mapped["Payment"] = relationship(back_populates="transactions")
