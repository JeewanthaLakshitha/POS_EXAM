from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routers import products, customers, orders

app = FastAPI(
    title="Book Shop",
    description="",
    version="1.0.0",
)


Base.metadata.create_all(bind=engine)

app.include_router(products.router)
app.include_router(customers.router)
app.include_router(orders.router)


@app.get("/")
def home():
    return {"message": "POS API is running", "book": "book"}
