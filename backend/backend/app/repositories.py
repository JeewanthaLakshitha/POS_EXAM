from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Category, CustomerOrder, LoyaltyCustomer, Product, OrderItem


def get_category(db: Session, category_id: int):
    return db.get(Category, category_id)


def get_product(db: Session, product_id: int, lock: bool = False):
    statement = select(Product).where(Product.product_id == product_id)
    if lock:
        statement = statement.with_for_update()
    return db.execute(statement).scalar_one_or_none()


def find_customer_by_mobile(db: Session, mobile_number: str, lock: bool = False):
    statement = select(LoyaltyCustomer).where(
        LoyaltyCustomer.mobile_number == mobile_number
    )
    if lock:
        statement = statement.with_for_update()
    return db.execute(statement).scalar_one_or_none()


def get_order(db: Session, order_id: int):
    statement = (
        select(CustomerOrder)
        .options(
            joinedload(CustomerOrder.customer),
            joinedload(CustomerOrder.items).joinedload(OrderItem.product),
        )
        .where(CustomerOrder.order_id == order_id)
    )
    return db.execute(statement).unique().scalar_one_or_none()
