from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.ride.ride_domain import (
    VehicleVerifyReviewRequest,
    VehicleVerifySubmitRequest,
    DriverAcceptRequest,
    OrderPublishRequest,
    VehicleCreateRequest,
    VehicleVerifyUpdateRequest,
    VehicleStatusUpdateRequest,
    VehicleUpdateRequest,
)
from backend.ride.ride_domain import create_vehicle as ride_create_vehicle
from backend.ride.ride_domain import delete_vehicle as ride_delete_vehicle
from backend.ride.ride_domain import driver_accept as ride_driver_accept
from backend.ride.ride_domain import list_vehicles as ride_list_vehicles
from backend.ride.ride_domain import (
    list_vehicle_verify_requests as ride_list_vehicle_verify_requests,
)
from backend.ride.ride_domain import (
    passenger_confirm as ride_passenger_confirm,
)
from backend.ride.ride_domain import publish_order as ride_publish_order
from backend.ride.ride_domain import search_orders as ride_search_orders
from backend.ride.ride_domain import (
    review_vehicle_verify_request as ride_review_vehicle_verify_request,
)
from backend.ride.ride_domain import (
    submit_vehicle_verify_request as ride_submit_vehicle_verify_request,
)
from backend.ride.ride_domain import (
    update_vehicle as ride_update_vehicle,
)
from backend.ride.ride_domain import (
    update_vehicle_status as ride_update_vehicle_status,
)
from backend.ride.ride_domain import (
    update_vehicle_verified as ride_update_vehicle_verified,
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


@app.patch("/api/vehicles/{vehicle_id}/verified")
def update_vehicle_verified(
    vehicle_id: int,
    payload: VehicleVerifyUpdateRequest,
    x_user_role: str = Header(default="user", alias="X-User-Role"),
):
    # 仅管理员可修改车辆认证状态。
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    return ride_update_vehicle_verified(vehicle_id, payload)


@app.post("/api/vehicles/{vehicle_id}/verify-request")
def submit_vehicle_verify_request(
    vehicle_id: int,
    payload: VehicleVerifySubmitRequest,
    x_user_id: str = Header(default="dev-user-1", alias="X-User-Id"),
):
    # 车主提交车辆认证资料。
    return ride_submit_vehicle_verify_request(vehicle_id, payload, x_user_id)


@app.get("/api/vehicles/verify-requests")
def list_vehicle_verify_requests(
    status: Optional[str] = Query(default="pending"),
    x_user_role: str = Header(default="user", alias="X-User-Role"),
):
    # 仅管理员可查看车辆认证申请。
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    return ride_list_vehicle_verify_requests(status)


@app.patch("/api/vehicles/verify-requests/{request_id}/review")
def review_vehicle_verify_request(
    request_id: int,
    payload: VehicleVerifyReviewRequest,
    x_user_id: str = Header(default="admin", alias="X-User-Id"),
    x_user_role: str = Header(default="user", alias="X-User-Role"),
):
    # 仅管理员可审核车辆认证资料。
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    return ride_review_vehicle_verify_request(request_id, payload, x_user_id)


@app.delete("/api/vehicles/{vehicle_id}")
def delete_vehicle(vehicle_id: int):
    # 删除车辆。
    return ride_delete_vehicle(vehicle_id)
