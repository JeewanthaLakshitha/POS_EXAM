 from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CustomerCreate, CustomerOut
from app.repositories import find_customer_by_mobile
from app.services import create_customer

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


@router.post("", response_model=CustomerOut, status_code=201)
def add_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    return create_customer(db, data)


@router.get("/lookup", response_model=CustomerOut)
def lookup_customer(mobileNumber: str, db: Session = Depends(get_db)):
    normalized = CustomerCreate.normalize_mobile(mobileNumber)
    customer = find_customer_by_mobile(db, normalized)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
