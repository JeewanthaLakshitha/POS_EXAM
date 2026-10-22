from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class ProductCreate(BaseModel):
    product_code: str = Field(min_length=1, max_length=40)
    product_name: str = Field(min_length=1, max_length=150)
    unit_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    available_quantity: int = Field(ge=0)
    active: bool = True
    category_id: int = Field(gt=0)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_code: str
    product_name: str
    unit_price: Decimal
    available_quantity: int
    active: bool
    category_id: int
    category_name: str


class CustomerCreate(BaseModel):
    mobile_number: str
    full_name: str = Field(min_length=1, max_length=150)
    email: Optional[EmailStr] = None

    @field_validator("mobile_number")
    @classmethod
    def normalize_mobile(cls, value: str) -> str:
        value = value.strip().replace(" ", "").replace("-", "")
        if value.startswith("07") and len(value) == 10 and value.isdigit():
            value = "+94" + value[1:]
        elif value.startswith("947") and len(value) == 11 and value.isdigit():
            value = "+" + value
        if len(value) != 12 or not value.startswith("+947") or not value[1:].isdigit():
            raise ValueError("Use a Sri Lankan mobile number such as 0771234567 or +94771234567")
        return value


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    mobile_number: str
    full_name: str
    email: Optional[str]
    loyalty_points: int
    registered_at: datetime


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    mobile_number: str
    full_name: str = Field(min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    items: List[OrderItemCreate] = Field(min_length=1)

    @field_validator("mobile_number")
    @classmethod
    def normalize_mobile(cls, value: str) -> str:
        return CustomerCreate.normalize_mobile(value)

    @model_validator(mode="after")
    def no_repeated_products(self):
        product_ids = [item.product_id for item in self.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("A product ID may only appear once in an order")
        return self


class OrderItemOut(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderOut(BaseModel):
    order_id: int
    customer_id: int
    customer_mobile: str
    order_date_time: datetime
    order_status: str
    total_amount: Decimal
    loyalty_points_earned: int
    customer_loyalty_points: int
    items: List[OrderItemOut]


class DailySummaryOut(BaseModel):
    business_date: str
    completed_orders: int
    units_sold: int
    revenue: Decimal
    loyalty_points_awarded: int
