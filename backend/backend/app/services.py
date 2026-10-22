from datetime import date
from decimal import Decimal, ROUND_FLOOR
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models import Category, CustomerOrder, LoyaltyCustomer, OrderItem, Product
from app import repositories
from app.schemas import CustomerCreate, OrderCreate, ProductCreate


def create_product(db: Session, data: ProductCreate):
    category = repositories.get_category(db, data.category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    if not category.active:
        raise HTTPException(status_code=400, detail="Cannot create a product in an inactive category")

    product = Product(**data.model_dump())
    db.add(product)
    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product code already exists")
    return product


def search_products(db: Session, name=None, min_price=None, max_price=None, category_id=None):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="minPrice cannot be greater than maxPrice")

    statement = select(Product).options(joinedload(Product.category))
    if name:
        statement = statement.where(Product.product_name.ilike(f"%{name}%"))
    if min_price is not None:
        statement = statement.where(Product.unit_price >= min_price)
    if max_price is not None:
        statement = statement.where(Product.unit_price <= max_price)
    if category_id is not None:
        statement = statement.where(Product.category_id == category_id)
    return db.execute(statement.order_by(Product.product_id)).scalars().all()


def create_customer(db: Session, data: CustomerCreate):
    existing = repositories.find_customer_by_mobile(db, data.mobile_number)
    if existing:
        raise HTTPException(status_code=409, detail="Customer mobile number already exists")
    customer = LoyaltyCustomer(
        mobile_number=data.mobile_number,
        full_name=data.full_name,
        email=str(data.email) if data.email else None,
        loyalty_points=0,
    )
    db.add(customer)
    try:
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Customer mobile number already exists")
    return customer


def place_order(db: Session, data: OrderCreate):
    """Process an order as one transaction; rollback everything if a step fails."""
    try:

        customer = repositories.find_customer_by_mobile(db, data.mobile_number, lock=True)
        if customer is None:
            customer = LoyaltyCustomer(
                mobile_number=data.mobile_number,
                full_name=data.full_name,
                email=str(data.email) if data.email else None,
                loyalty_points=0,
            )
            db.add(customer)
            db.flush()


        item_inputs = sorted(data.items, key=lambda item: item.product_id)
        products = {}
        for item in item_inputs:
            product = repositories.get_product(db, item.product_id, lock=True)
            if product is None:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            if not product.active:
                raise HTTPException(status_code=400, detail=f"Product {product.product_name} is inactive")
            if product.available_quantity < item.quantity:
                raise HTTPException(status_code=400, detail=f"Not enough stock for {product.product_name}")
            products[item.product_id] = product

        total = Decimal("0.00")
        order_items = []

        for item in data.items:
            product = products[item.product_id]
            unit_price = Decimal(product.unit_price).quantize(Decimal("0.01"))
            subtotal = (unit_price * item.quantity).quantize(Decimal("0.01"))
            total += subtotal
            order_items.append(
                OrderItem(
                    product=product,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )
            )

        points = int((total / Decimal("100")).to_integral_value(rounding=ROUND_FLOOR))
        order = CustomerOrder(
            customer=customer,
            order_status="COMPLETED",
            total_amount=total,
            loyalty_points_earned=points,
            items=order_items,
        )
        db.add(order)

        for item in data.items:
            products[item.product_id].available_quantity -= item.quantity

        customer.loyalty_points += points
        db.commit()
        db.refresh(order)
        db.refresh(customer)
        return order
    except Exception:
        db.rollback()
        raise


def daily_summary(db: Session, business_date: date):

    order_statement = select(
        func.count(CustomerOrder.order_id),
        func.coalesce(func.sum(CustomerOrder.total_amount), 0),
        func.coalesce(func.sum(CustomerOrder.loyalty_points_earned), 0),
    ).where(
        func.date(CustomerOrder.order_date_time) == business_date,
        CustomerOrder.order_status == "COMPLETED",
    )
    order_count, revenue, points = db.execute(order_statement).one()

    item_statement = (
        select(func.coalesce(func.sum(OrderItem.quantity), 0))
        .join(CustomerOrder, OrderItem.order_id == CustomerOrder.order_id)
        .where(
            func.date(CustomerOrder.order_date_time) == business_date,
            CustomerOrder.order_status == "COMPLETED",
        )
    )
    units_sold = db.execute(item_statement).scalar_one()

    return {
        "business_date": business_date.isoformat(),
        "completed_orders": order_count,
        "units_sold": units_sold,
        "revenue": Decimal(revenue),
        "loyalty_points_awarded": points,
    }
