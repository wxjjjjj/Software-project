from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.ride.ride_domain import DriverAcceptRequest, OrderPublishRequest
from backend.ride.ride_domain import driver_accept as ride_driver_accept
from backend.ride.ride_domain import (
    passenger_confirm as ride_passenger_confirm,
)
from backend.ride.ride_domain import publish_order as ride_publish_order
from backend.ride.ride_domain import search_orders as ride_search_orders

app = FastAPI(title="Ride Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ride"}


@app.get("/api/orders/search")
def search_orders():
    return ride_search_orders()


@app.post("/api/orders")
def publish_order(payload: OrderPublishRequest):
    return ride_publish_order(payload)


@app.post("/api/orders/{order_id}/accept-by-driver")
def driver_accept(order_id: int, payload: DriverAcceptRequest):
    return ride_driver_accept(order_id, payload)


@app.post("/api/orders/{order_id}/confirm-by-passenger")
def passenger_confirm(order_id: int):
    return ride_passenger_confirm(order_id)
