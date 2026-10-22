
from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer,
    Numeric, String, func
)
from sqlalchemy.orm import relationship

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True)
    category_code = Column(String(40), unique=True, nullable=False)
    category_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    active = Column(Boolean, nullable=False, default=True)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("unit_price > 0", name="ck_product_price_positive"),
        CheckConstraint("available_quantity >= 0", name="ck_product_stock_nonnegative"),
    )

    product_id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(40), unique=True, nullable=False)
    product_name = Column(String(150), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    available_quantity = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    category_id = Column(
        Integer, ForeignKey("categories.category_id"), nullable=False
    )

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")


class LoyaltyCustomer(Base):
    __tablename__ = "loyalty_customers"
    __table_args__ = (
        CheckConstraint("loyalty_points >= 0", name="ck_customer_points_nonnegative"),
    )

    customer_id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String(12), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=True)
    loyalty_points = Column(Integer, nullable=False, default=0)
    registered_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    orders = relationship("CustomerOrder", back_populates="customer")


class CustomerOrder(Base):
    __tablename__ = "customer_orders"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_order_total_nonnegative"),
        CheckConstraint("loyalty_points_earned >= 0", name="ck_order_points_nonnegative"),
    )

    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer, ForeignKey("loyalty_customers.customer_id"), nullable=False
    )
    order_date_time = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    order_status = Column(String(20), nullable=False, default="COMPLETED")
    total_amount = Column(Numeric(12, 2), nullable=False)
    loyalty_points_earned = Column(Integer, nullable=False, default=0)

    customer = relationship("LoyaltyCustomer", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_item_quantity_positive"),
        CheckConstraint("unit_price > 0", name="ck_item_price_positive"),
        CheckConstraint("subtotal >= 0", name="ck_item_subtotal_nonnegative"),
    )

    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer, ForeignKey("customer_orders.order_id"), nullable=False
    )
    product_id = Column(
        Integer, ForeignKey("products.product_id"), nullable=False
    )
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)

    order = relationship("CustomerOrder", back_populates="items")
    product = relationship("Product", back_populates="order_items")
