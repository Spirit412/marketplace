from src.models.base import Base, CreatedAtMixin, SoftDeleteMixin, TimestampMixin

import uuid
from src.core.datatype import uuid7

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship



class Warehouse(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        UniqueConstraint("seller_id", "name", name="uq_warehouse_seller_name"),
        {"schema": "inventory", "comment": "Склад продавца"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7, comment="Первичный ключ склада"
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, comment="Продавец-владелец склада")
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="Название склада")
    address: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="Адрес склада")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", comment="Часовой пояс склада")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="Признак активности склада")

    stock_items: Mapped[list["StockItem"]] = relationship(
        back_populates="warehouse", lazy="selectin"
    )


class StockItem(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "stock_items"
    __table_args__ = {"schema": "inventory", "comment": "Остаток товара на конкретном складе"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7, comment="Первичный ключ остатка"
    )
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, comment="Товар (id из catalog-service)")
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory.warehouses.id", ondelete="CASCADE"), nullable=False, comment="Склад (fk на warehouses.id)"
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Общее количество на складе")
    reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Зарезервированное количество")

    warehouse: Mapped[Warehouse] = relationship(back_populates="stock_items")
    movements: Mapped[list["StockMovement"]] = relationship(
        back_populates="stock_item", lazy="selectin"
    )

    @property
    def available(self) -> int:
        return self.quantity - self.reserved


class StockMovement(CreatedAtMixin, Base):
    __tablename__ = "stock_movements"
    __table_args__ = {"schema": "inventory", "comment": "Движение товара по складу (приход/расход/резерв/списание) — аудиторский след"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7, comment="Первичный ключ движения"
    )
    stock_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory.stock_items.id", ondelete="CASCADE"), nullable=False, comment="Остаток, к которому относится движение"
    )
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="Тип движения (receipt/reserve/release/shipment/adjustment/return)")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="Количество в движении")
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="Тип связанной сущности (order, seed, cleanup...)")
    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, comment="Идентификатор связанной сущности (например, id заказа)"
    )

    stock_item: Mapped[StockItem] = relationship(back_populates="movements")
