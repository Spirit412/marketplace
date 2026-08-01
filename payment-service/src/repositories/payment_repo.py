import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.payment import Payment, Transaction


class PaymentRepo:
    """Async repository for Payment and Transaction models.

    Soft-deleted payments are hidden from reads unless explicitly requested.
    """

    async def create(self, session: AsyncSession, payment: Payment) -> Payment:
        session.add(payment)
        await session.flush()
        await session.refresh(payment, attribute_names=["transactions"])
        return payment

    async def get_by_uuid(
        self, session: AsyncSession, uuid_value: uuid.UUID
    ) -> Payment | None:
        stmt = (
            select(Payment)
            .where(Payment.id == uuid_value, Payment.is_delete.is_(False))
            .options(selectinload(Payment.transactions))
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_order_id(
        self, session: AsyncSession, order_id: uuid.UUID
    ) -> Payment | None:
        stmt = (
            select(Payment)
            .where(Payment.order_id == order_id, Payment.is_delete.is_(False))
            .options(selectinload(Payment.transactions))
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_gateway_payment_id(
        self, session: AsyncSession, gateway_payment_id: str
    ) -> Payment | None:
        stmt = (
            select(Payment)
            .where(
                Payment.gateway_payment_id == gateway_payment_id,
                Payment.is_delete.is_(False),
            )
            .options(selectinload(Payment.transactions))
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_idempotency_key(
        self, session: AsyncSession, key: str
    ) -> Payment | None:
        stmt = (
            select(Payment)
            .where(Payment.idempotency_key == key, Payment.is_delete.is_(False))
            .options(selectinload(Payment.transactions))
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def update_status(
        self, session: AsyncSession, payment: Payment, new_status: str
    ) -> Payment:
        payment.status = new_status
        await session.flush()
        # updated_at is server-side (onupdate=func.now()) — flush() alone
        # leaves it expired on the Python object; the next (synchronous)
        # attribute read, e.g. Pydantic serializing the response, would need
        # to lazy-load it and fail with MissingGreenlet outside an await.
        await session.refresh(payment)
        return payment

    async def add_transaction(
        self, session: AsyncSession, transaction: Transaction
    ) -> Transaction:
        session.add(transaction)
        await session.flush()
        return transaction
