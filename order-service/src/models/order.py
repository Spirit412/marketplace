from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.datatype import uuid7
from src.models.base import Base, SoftDeleteMixin, TimestampMixin


class Order(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": "order", "comment": "Заказ покупателя"}

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ заказа"
    )
    user_uuid: Mapped[uuid.UUID] = mapped_column(
        index=True, comment="Покупатель, оформивший заказ"
    )
    seller_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True, comment="Продавец (если заказ одного продавца)"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="Статус заказа (pending/confirmed/paid/shipped/delivered/cancelled)",
    )
    subtotal: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Сумма позиций без налогов и доставки, в минорных единицах валюты",
    )
    tax: Mapped[int] = mapped_column(
        Integer, default=0, comment="Сумма налога, в минорных единицах валюты"
    )
    discount: Mapped[int] = mapped_column(
        Integer, default=0, comment="Сумма скидки, в минорных единицах валюты"
    )
    shipping: Mapped[int] = mapped_column(
        Integer, default=0, comment="Стоимость доставки, в минорных единицах валюты"
    )
    total: Mapped[int] = mapped_column(
        Integer, default=0, comment="Итоговая сумма заказа, в минорных единицах валюты"
    )
    currency: Mapped[str] = mapped_column(
        String(3), default="RUB", comment="Код валюты (ISO 4217)"
    )
    tax_strategy: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="Стратегия расчёта налога (регион)"
    )
    payment_method: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Способ оплаты"
    )
    shipping_address: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="Адрес доставки (JSON)"
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        comment="Ключ идемпотентности запроса создания заказа",
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Примечание к заказу"
    )

    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    status_history: Mapped[list[OrderStatusHistory]] = relationship(
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = {
        "schema": "order",
        "comment": "Позиция заказа (товар, количество, цена на момент заказа)",
    }

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ позиции"
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order.orders.id", ondelete="CASCADE"),
        nullable=False,
        comment="Заказ (fk на orders.id)",
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        index=True, comment="Товар (id из catalog-service)"
    )
    product_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Название товара на момент заказа"
    )
    price: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Цена за единицу на момент заказа, в минорных единицах валюты",
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Количество товара в заказе"
    )
    seller_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True, comment="Продавец товара"
    )
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
        comment="Склад, с которого зарезервирован товар (fk на inventory.warehouses.id)",
    )

    order: Mapped[Order] = relationship(back_populates="items")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    __table_args__ = {"schema": "order", "comment": "История смены статусов заказа"}

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ записи истории"
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order.orders.id", ondelete="CASCADE"),
        nullable=False,
        comment="Заказ (fk на orders.id)",
    )
    from_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Статус до перехода"
    )
    to_status: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Статус после перехода"
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Дата и время смены статуса",
    )
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True, comment="Пользователь, инициировавший смену статуса"
    )
    comment: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Комментарий к смене статуса"
    )

    order: Mapped[Order] = relationship(back_populates="status_history")
