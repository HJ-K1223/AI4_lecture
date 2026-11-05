"""상품 선택·장바구니·주문·결제 입력 검증."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

Quantity = Annotated[StrictInt, Field(ge=1, le=99)]


class CartItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: UUID
    quantity: Quantity


class QuantityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quantity: Quantity


class OrderInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cart_id: UUID
    quote: str = Field(min_length=1, max_length=4096)
    recipient_name: str = Field(min_length=1, max_length=80)
    recipient_phone: str = Field(min_length=1, max_length=30)
    shipping_address: str = Field(min_length=1, max_length=500)

    @field_validator("recipient_name", "recipient_phone", "shipping_address", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class PaymentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: UUID
    idempotency_key: UUID
    method: Literal["MOCK_CARD"] = "MOCK_CARD"
