from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware

from backend.ride.ride_domain import (
    DriverAcceptRequest,
    OrderPublishRequest,
    VehicleCreateRequest,
    VehicleStatusUpdateRequest,
    VehicleUpdateRequest,
)
from backend.ride.ride_domain import create_vehicle as ride_create_vehicle
from backend.ride.ride_domain import delete_vehicle as ride_delete_vehicle
from backend.ride.ride_domain import driver_accept as ride_driver_accept
from backend.ride.ride_domain import list_vehicles as ride_list_vehicles
from backend.ride.ride_domain import (
    passenger_confirm as ride_passenger_confirm,
)
from backend.ride.ride_domain import publish_order as ride_publish_order
from backend.ride.ride_domain import search_orders as ride_search_orders
from backend.ride.ride_domain import (
    update_vehicle as ride_update_vehicle,
)
from backend.ride.ride_domain import (
    update_vehicle_status as ride_update_vehicle_status,
)

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


@app.get("/api/vehicles")
def list_vehicles(x_user_id: str = Header(default="dev-user-1", alias="X-User-Id")):
    # 按当前登录用户查询车辆。
    return ride_list_vehicles(x_user_id)


@app.post("/api/vehicles")
def create_vehicle(
    payload: VehicleCreateRequest,
    x_user_id: str = Header(default="dev-user-1", alias="X-User-Id"),
):
    # 新增车辆。
    return ride_create_vehicle(payload, x_user_id)


@app.put("/api/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: int, payload: VehicleUpdateRequest):
    # 编辑车辆基础信息。
    return ride_update_vehicle(vehicle_id, payload)


@app.patch("/api/vehicles/{vehicle_id}/status")
def update_vehicle_status(vehicle_id: int, payload: VehicleStatusUpdateRequest):
    # 切换车辆状态（可用/停用）。
    return ride_update_vehicle_status(vehicle_id, payload)


@app.delete("/api/vehicles/{vehicle_id}")
def delete_vehicle(vehicle_id: int):
    # 删除车辆。
    return ride_delete_vehicle(vehicle_id)
