from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ProductCreate, ProductOut
from app.services import create_product, search_products

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


def product_to_output(product):
    return {
        "product_id": product.product_id,
        "product_code": product.product_code,
        "product_name": product.product_name,
        "unit_price": product.unit_price,
        "available_quantity": product.available_quantity,
        "active": product.active,
        "category_id": product.category_id,
        "category_name": product.category.category_name,
    }


@router.post("", response_model=ProductOut, status_code=201)
def add_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = create_product(db, data)
    # Load the category relationship before making the response.
    db.refresh(product)
    return product_to_output(product)


@router.get("", response_model=List[ProductOut])
def get_products(
    name: Optional[str] = None,
    minPrice: Optional[Decimal] = Query(default=None, ge=0),
    maxPrice: Optional[Decimal] = Query(default=None, ge=0),
    categoryId: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    products = search_products(db, name, minPrice, maxPrice, categoryId)
    return [product_to_output(product) for product in products]
