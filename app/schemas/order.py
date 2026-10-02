from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    quantity: int = Field(ge=1, le=100)


class RazorpayPaymentProof(BaseModel):
    razorpay_order_id: str = Field(min_length=1, max_length=100)
    razorpay_payment_id: str = Field(min_length=1, max_length=100)
    razorpay_signature: str = Field(min_length=1, max_length=500)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1, max_length=100)
    expected_total: Decimal = Field(gt=0)
    payment: RazorpayPaymentProof


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    variant_label: str | None
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = {
        "from_attributes": True,
    }


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    status: str
    subtotal: Decimal
    shipping_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItemResponse]


class OrderSummaryResponse(BaseModel):
    total_orders: int
    processing_orders: int
    shipped_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_amount: Decimal
