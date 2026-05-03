"""
订单域 FastAPI 入口（端口 8002）
负责人：hws
"""
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.ride.ride_domain import (
    AcceptOrderRequest,
    CompleteOrderRequest,
    OrderPublishRequest,
    OrderUpdateRequest,
    VehicleCreateRequest,
    VehicleStatusUpdateRequest,
    VehicleUpdateRequest,
    VehicleVerifyReviewRequest,
    VehicleVerifySubmitRequest,
    VehicleVerifyUpdateRequest,
    accept_order,
    cancel_order,
    complete_order,
    create_vehicle,
    delete_vehicle,
    get_order_detail,
    join_order,
    list_vehicle_verify_requests,
    list_orders,
    list_vehicles,
    publish_order,
    review_vehicle_verify_request,
    search_orders,
    submit_vehicle_verify_request,
    update_order,
    update_vehicle,
    update_vehicle_status,
    update_vehicle_verified,
)

app = FastAPI(title="Ride Service", version="1.0.0")

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


# ── 订单接口（注意：/orders/search 必须在 /orders/{order_id} 之前注册） ────────

@app.post("/api/orders")
def api_publish_order(
    payload: OrderPublishRequest,
    x_user_id: str = Header(default="dev-user-1", alias="X-User-Id"),
):
    """拼车人发布订单（含标签）"""
    return publish_order(payload, x_user_id)


@app.get("/api/orders/search")
def api_search_orders(
    start_loc: Optional[str] = Query(default=None),
    end_loc: Optional[str] = Query(default=None),
    time_from: Optional[str] = Query(default=None),
    time_to: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),  # 逗号分隔, e.g. "静音,禁烟"
):
    """搜索订单（只返回 published/full 状态），支持标签筛选"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    return search_orders(start_loc, end_loc, time_from, time_to, tag_list)


@app.get("/api/orders")
def api_list_orders(
    passenger_id: Optional[str] = Query(default=None),
    owner_id: Optional[str] = Query(default=None),
):
    """
    查看订单列表：
    - ?passenger_id=xxx  → 该乘客发布/参与的订单
    - ?owner_id=xxx      → 该车主已接订单
    - 无参数             → 全部订单（管理员用）
    """
    return list_orders(passenger_id, owner_id)


@app.get("/api/orders/{order_id}")
def api_get_order_detail(order_id: str):
    """查看订单详情（含剩余座位、标签）"""
    return get_order_detail(order_id)


@app.put("/api/orders/{order_id}")
def api_update_order(
    order_id: str,
    payload: OrderUpdateRequest,
    x_user_id: str = Header(default="dev-user-1", alias="X-User-Id"),
):
    """修改订单信息（仅限 published 状态，且只有发单人可改）"""
    return update_order(order_id, payload, x_user_id)


@app.post("/api/orders/{order_id}/cancel")
def api_cancel_order(
    order_id: str,
    x_user_id: str = Header(default="dev-user-1", alias="X-User-Id"),
    x_user_role: str = Header(default="user", alias="X-User-Role"),
):
    """取消订单（发单人、已接车主、已参与乘客、管理员均可）"""
    return cancel_order(order_id, x_user_id, is_admin=(x_user_role == "admin"))


@app.post("/api/orders/{order_id}/join")
def api_join_order(
    order_id: str,
    x_user_id: str = Header(default="dev-user-1", alias="X-User-Id"),
):
    """拼车人加入订单（仅限 published 状态）"""
    return join_order(order_id, x_user_id)


@app.post("/api/orders/{order_id}/accept")
def api_accept_order(
    order_id: str,
    payload: AcceptOrderRequest,
    x_user_id: str = Header(default="dev-owner-1", alias="X-User-Id"),
):
    """车主接单（仅限 published/full 状态）"""
    return accept_order(order_id, payload, x_user_id)


@app.post("/api/orders/{order_id}/complete")
def api_complete_order(
    order_id: str,
    payload: CompleteOrderRequest,
):
    """标记订单完成（域3支付成功后回调，仅限 locked 状态）"""
    return complete_order(order_id)


@app.get("/api/vehicles")
def api_list_vehicles(
    x_user_id: str = Header(default="dev-user-1", alias="X-User-Id"),
):
    """查询当前车主名下所有可用车辆"""
    return list_vehicles(x_user_id)


@app.post("/api/vehicles")
def api_create_vehicle(
    payload: VehicleCreateRequest,
    x_user_id: str = Header(default="dev-user-1", alias="X-User-Id"),
):
    """新增当前车主车辆"""
    return create_vehicle(payload, x_user_id)


@app.get("/api/vehicles/verify-requests")
def api_list_vehicle_verify_requests(
    status: Optional[str] = Query(default="pending"),
    x_user_role: str = Header(default="user", alias="X-User-Role"),
):
    """管理员查看车辆认证申请"""
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    return list_vehicle_verify_requests(status)


@app.patch("/api/vehicles/verify-requests/{request_id}/review")
def api_review_vehicle_verify_request(
    request_id: str,
    payload: VehicleVerifyReviewRequest,
    x_user_id: str = Header(default="admin", alias="X-User-Id"),
    x_user_role: str = Header(default="user", alias="X-User-Role"),
):
    """管理员审核车辆认证申请"""
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    return review_vehicle_verify_request(request_id, payload, x_user_id)


@app.put("/api/vehicles/{vehicle_id}")
def api_update_vehicle(vehicle_id: str, payload: VehicleUpdateRequest):
    """编辑车辆基础信息"""
    return update_vehicle(vehicle_id, payload)


@app.patch("/api/vehicles/{vehicle_id}/status")
def api_update_vehicle_status(vehicle_id: str, payload: VehicleStatusUpdateRequest):
    """切换车辆状态"""
    return update_vehicle_status(vehicle_id, payload)


@app.patch("/api/vehicles/{vehicle_id}/verified")
def api_update_vehicle_verified(
    vehicle_id: str,
    payload: VehicleVerifyUpdateRequest,
    x_user_role: str = Header(default="user", alias="X-User-Role"),
):
    """管理员直接修改车辆认证状态"""
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    return update_vehicle_verified(vehicle_id, payload)


@app.post("/api/vehicles/{vehicle_id}/verify-request")
def api_submit_vehicle_verify_request(
    vehicle_id: str,
    payload: VehicleVerifySubmitRequest,
    x_user_id: str = Header(default="dev-user-1", alias="X-User-Id"),
):
    """车主提交车辆认证资料"""
    return submit_vehicle_verify_request(vehicle_id, payload, x_user_id)


@app.delete("/api/vehicles/{vehicle_id}")
def api_delete_vehicle(vehicle_id: str):
    """删除车辆"""
    return delete_vehicle(vehicle_id)
