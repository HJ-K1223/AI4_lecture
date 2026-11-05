"""shoppingmall 스키마 매핑. 테이블 생성·제약조건의 기준은 db/schema.sql입니다."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, Computed, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class IdentityMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now()
    )


class Member(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "members"

    email: Mapped[str] = mapped_column(String(254))
    password_hash: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(10), server_default="ACTIVE")
    auth_version: Mapped[int] = mapped_column(Integer, server_default="1")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Product(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, server_default="")
    price: Mapped[int] = mapped_column(BigInteger)
    stock: Mapped[int] = mapped_column(Integer, server_default="0")
    image_path: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class Order(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    member_id: Mapped[UUID] = mapped_column(ForeignKey("shoppingmall.members.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(10), server_default="CART")
    currency: Mapped[str] = mapped_column(String(3), server_default="KRW")
    total_amount: Mapped[int] = mapped_column(BigInteger, server_default="0")
    recipient_name: Mapped[str | None] = mapped_column(String(80))
    recipient_phone: Mapped[str | None] = mapped_column(String(30))
    shipping_address: Mapped[str | None] = mapped_column(String(500))
    ordered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OrderItem(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[UUID] = mapped_column(ForeignKey("shoppingmall.orders.id", ondelete="RESTRICT"))
    product_id: Mapped[UUID] = mapped_column(ForeignKey("shoppingmall.products.id", ondelete="RESTRICT"))
    product_name: Mapped[str] = mapped_column(String(150))
    unit_price: Mapped[int] = mapped_column(BigInteger)
    quantity: Mapped[int] = mapped_column(Integer)
    line_total: Mapped[int] = mapped_column(BigInteger, Computed("unit_price * quantity", persisted=True))


class Payment(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    order_id: Mapped[UUID] = mapped_column(ForeignKey("shoppingmall.orders.id", ondelete="RESTRICT"))
    provider: Mapped[str] = mapped_column(String(30), server_default="MOCK")
    method: Mapped[str] = mapped_column(String(30), server_default="MOCK_CARD")
    status: Mapped[str] = mapped_column(String(10), server_default="PENDING")
    amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), server_default="KRW")
    idempotency_key: Mapped[UUID]
    transaction_id: Mapped[str | None] = mapped_column(String(150))
    failure_code: Mapped[str | None] = mapped_column(String(50))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
