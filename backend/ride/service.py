"""
订单域 FastAPI 入口（端口 8002）
负责人：hws
"""
from typing import Optional

from fastapi import FastAPI, Header, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.ride.ride_domain import (
    AcceptOrderRequest,
    CompleteOrderRequest,
    OrderPublishRequest,
    OrderUpdateRequest,
    accept_order,
    cancel_order,
    complete_order,
    get_order_detail,
    join_order,
    list_orders,
    list_vehicles,
    publish_order,
    search_orders,
    update_order,
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
