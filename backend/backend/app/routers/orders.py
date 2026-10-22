from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import get_order
from app.schemas import OrderCreate, OrderOut, DailySummaryOut
from app.services import place_order, daily_summary

router = APIRouter(prefix="/api/v1", tags=["Orders"])


def order_to_output(order):
    return {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "customer_mobile": order.customer.mobile_number,
        "order_date_time": order.order_date_time,
        "order_status": order.order_status,
        "total_amount": order.total_amount,
        "loyalty_points_earned": order.loyalty_points_earned,
        "customer_loyalty_points": order.customer.loyalty_points,
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
            for item in order.items
        ],
    }


@router.post("/orders", response_model=OrderOut, status_code=201)
def add_order(data: OrderCreate, db: Session = Depends(get_db)):
    order = place_order(db, data)
    # Re-query to load customer, items and product names for the response.
    order = get_order(db, order.order_id)
    return order_to_output(order)


@router.get("/orders/{order_id}", response_model=OrderOut)
def read_order(order_id: int, db: Session = Depends(get_db)):
    order = get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_to_output(order)


@router.get("/reports/daily", response_model=DailySummaryOut)
def get_daily_summary(
    businessDate: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
):
    return daily_summary(db, businessDate)
