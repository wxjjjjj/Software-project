"""
订单域业务逻辑
负责人：hws（订单核心）

覆盖接口：
  1.  POST   /api/orders              发布订单
  2.  GET    /api/orders/search       搜索订单
  3.  GET    /api/orders              按用户列出订单
  4.  GET    /api/orders/{id}         订单详情
  5.  PUT    /api/orders/{id}         修改订单（仅 published）
  6.  POST   /api/orders/{id}/cancel  取消订单
  7.  POST   /api/orders/{id}/join    拼车人加入
  8.  POST   /api/orders/{id}/accept  车主接单
  9.  POST   /api/orders/{id}/complete 标记完成（域3回调）
  10. GET    /api/orders/all          管理员查看全部订单（alias → list_orders 无参数）
"""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from backend.common.config import RIDE_USE_MOCK
from backend.ride.ride_db import get_ride_conn

# ── Pydantic Request Models ───────────────────────────────────────────────────


class OrderPublishRequest(BaseModel):
    start_loc: str
    end_loc: str
    depart_time_from: str       # ISO datetime, e.g. "2026-04-15T08:00:00"
    depart_time_to: str
    group_size: int = 1         # 发单方实际人数（含自己），决定 seats_joined 初始值
    extra_seats: int = 0        # 还愿意带几人，seats_needed = group_size + extra_seats
    expected_price: float = 0.0
    tags: List[str] = []

    @property
    def seats_needed(self) -> int:
        return max(1, self.group_size + self.extra_seats)


class OrderUpdateRequest(BaseModel):
    start_loc: Optional[str] = None
    end_loc: Optional[str] = None
    depart_time_from: Optional[str] = None
    depart_time_to: Optional[str] = None
    seats_needed: Optional[int] = None
    expected_price: Optional[float] = None
    tags: Optional[List[str]] = None


class AcceptOrderRequest(BaseModel):
    vehicle_id: str


class CompleteOrderRequest(BaseModel):
    operator: str = "domain3"


# ── Mock Data Store ───────────────────────────────────────────────────────────

def _new_id() -> str:
    return str(uuid.uuid4())[:12]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# 预置种子数据，方便开发调试
_ORDERS: dict = {
    "ord-seed-001": {
        "order_id": "ord-seed-001",
        "passenger_id": "dev-user-1",
        "start_loc": "软件园",
        "end_loc": "大学城",
        "depart_time_from": "2026-04-15T08:00:00",
        "depart_time_to": "2026-04-15T09:00:00",
        "seats_needed": 3,
        "seats_joined": 1,
        "expected_price": 45.00,
        "owner_id": None,
        "vehicle_id": None,
        "locked_time": None,
        "status": "published",
        "created_at": "2026-04-13T10:00:00",
        "updated_at": "2026-04-13T10:00:00",
    },
    "ord-seed-002": {
        "order_id": "ord-seed-002",
        "passenger_id": "dev-user-2",
        "start_loc": "天河客运站",
        "end_loc": "广州南站",
        "depart_time_from": "2026-04-16T14:00:00",
        "depart_time_to": "2026-04-16T15:00:00",
        "seats_needed": 2,
        "seats_joined": 1,
        "expected_price": 60.00,
        "owner_id": None,
        "vehicle_id": None,
        "locked_time": None,
        "status": "published",
        "created_at": "2026-04-13T09:00:00",
        "updated_at": "2026-04-13T09:00:00",
    },
    "ord-seed-003": {
        "order_id": "ord-seed-003",
        "passenger_id": "dev-user-1",
        "start_loc": "珠江新城",
        "end_loc": "广州白云机场",
        "depart_time_from": "2026-04-17T06:00:00",
        "depart_time_to": "2026-04-17T07:00:00",
        "seats_needed": 3,
        "seats_joined": 3,
        "expected_price": 80.00,
        "owner_id": "dev-owner-1",
        "vehicle_id": "veh-mock-001",
        "locked_time": "2026-04-13T12:00:00",
        "status": "locked",
        "created_at": "2026-04-13T08:00:00",
        "updated_at": "2026-04-13T12:00:00",
    },
    "ord-seed-004": {
        "order_id": "ord-seed-004",
        "passenger_id": "dev-user-3",
        "start_loc": "南门",
        "end_loc": "广州南站",
        "depart_time_from": "2026-04-18T10:00:00",
        "depart_time_to": "2026-04-18T11:00:00",
        "seats_needed": 2,
        "seats_joined": 1,
        "expected_price": 25.00,
        "owner_id": None,
        "vehicle_id": None,
        "locked_time": None,
        "status": "published",
        "created_at": "2026-04-13T11:00:00",
        "updated_at": "2026-04-13T11:00:00",
    },
}

_TAGS: dict = {
    "tag-s1": {"tag_id": "tag-s1", "order_id": "ord-seed-001", "tag_content": "静音"},
    "tag-s2": {"tag_id": "tag-s2", "order_id": "ord-seed-001", "tag_content": "禁烟"},
    "tag-s3": {"tag_id": "tag-s3", "order_id": "ord-seed-002", "tag_content": "宠物友好"},
    "tag-s4": {"tag_id": "tag-s4", "order_id": "ord-seed-003", "tag_content": "早高峰"},
    "tag-s5": {"tag_id": "tag-s5", "order_id": "ord-seed-003", "tag_content": "不绕路"},
    "tag-s6": {"tag_id": "tag-s6", "order_id": "ord-seed-004", "tag_content": "准时出发"},
    "tag-s7": {"tag_id": "tag-s7", "order_id": "ord-seed-004", "tag_content": "禁烟"},
}

_PASSENGERS: dict = {
    "rec-s1": {
        "record_id": "rec-s1", "order_id": "ord-seed-001",
        "passenger_id": "dev-user-1", "join_time": "2026-04-13T10:00:00",
        "pay_status": "pending",
    },
    "rec-s2": {
        "record_id": "rec-s2", "order_id": "ord-seed-002",
        "passenger_id": "dev-user-2", "join_time": "2026-04-13T09:00:00",
        "pay_status": "pending",
    },
    "rec-s3": {
        "record_id": "rec-s3", "order_id": "ord-seed-003",
        "passenger_id": "dev-user-1", "join_time": "2026-04-13T08:00:00",
        "pay_status": "pending",
    },
    "rec-s4": {
        "record_id": "rec-s4", "order_id": "ord-seed-003",
        "passenger_id": "dev-user-3", "join_time": "2026-04-13T08:30:00",
        "pay_status": "pending",
    },
    "rec-s5": {
        "record_id": "rec-s5", "order_id": "ord-seed-003",
        "passenger_id": "dev-user-4", "join_time": "2026-04-13T09:00:00",
        "pay_status": "pending",
    },
}


# 车辆 mock 数据（dev 环境，含 dev-user-1 和 dev-owner-1 各自的车）
_VEHICLES: dict = {
    "veh-mock-001": {
        "vehicle_id": "veh-mock-001",
        "owner_id": "dev-owner-1",
        "plate_no": "粤A·88888",
        "brand": "丰田 凯美瑞",
        "color": "珍珠白",
        "seat_capacity": 5,
        "status": "available",
    },
    "veh-mock-002": {
        "vehicle_id": "veh-mock-002",
        "owner_id": "dev-user-1",
        "plate_no": "粤B·12345",
        "brand": "本田 雅阁",
        "color": "深空黑",
        "seat_capacity": 5,
        "status": "available",
    },
    "veh-mock-003": {
        "vehicle_id": "veh-mock-003",
        "owner_id": "dev-user-1",
        "plate_no": "粤C·67890",
        "brand": "大众 帕萨特",
        "color": "银色",
        "seat_capacity": 5,
        "status": "available",
    },
}


# ── Mock Helpers ──────────────────────────────────────────────────────────────

def _mock_get_tags(order_id: str) -> List[str]:
    return [t["tag_content"] for t in _TAGS.values() if t["order_id"] == order_id]


def _mock_set_tags(order_id: str, tag_list: List[str]) -> None:
    to_del = [k for k, v in _TAGS.items() if v["order_id"] == order_id]
    for k in to_del:
        del _TAGS[k]
    for content in tag_list:
        tid = _new_id()
        _TAGS[tid] = {"tag_id": tid, "order_id": order_id, "tag_content": content}


def _mock_format(order: dict) -> dict:
    o = dict(order)
    o["tags"] = _mock_get_tags(order["order_id"])
    o["remaining_seats"] = max(0, order["seats_needed"] - order["seats_joined"])
    return o


# ── DB Helpers ────────────────────────────────────────────────────────────────

def _db_get_tags(cursor, order_id: str) -> List[str]:
    cursor.execute("SELECT tag_content FROM order_tag WHERE order_id = %s", (order_id,))
    return [row["tag_content"] for row in cursor.fetchall()]


def _iso(val) -> Optional[str]:
    """Convert datetime to ISO string if needed."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat(timespec="seconds")
    return str(val)


def _db_format(row: dict, tags: List[str]) -> dict:
    return {
        "order_id": row["id"],
        "passenger_id": row["passenger_id"],
        "start_loc": row["start_loc"],
        "end_loc": row["end_loc"],
        "depart_time_from": _iso(row["depart_time_from"]),
        "depart_time_to": _iso(row["depart_time_to"]),
        "seats_needed": row["seats_needed"],
        "seats_joined": row["seats_joined"],
        "remaining_seats": max(0, row["seats_needed"] - row["seats_joined"]),
        "expected_price": float(row["expected_price"]),
        "owner_id": row["owner_id"],
        "vehicle_id": row["vehicle_id"],
        "locked_time": _iso(row["locked_time"]),
        "status": row["status"],
        "created_at": _iso(row["created_at"]),
        "updated_at": _iso(row["updated_at"]),
        "tags": tags,
    }


# ── 1. 发布订单 ────────────────────────────────────────────────────────────────

def publish_order(payload: OrderPublishRequest, user_id: str) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    oid = str(uuid.uuid4())
                    cursor.execute(
                        """INSERT INTO orders
                           (id, passenger_id, start_loc, end_loc,
                            depart_time_from, depart_time_to,
                            seats_needed, seats_joined, expected_price,
                            status, created_at, updated_at)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'published',NOW(),NOW())""",
                        (oid, user_id, payload.start_loc, payload.end_loc,
                         payload.depart_time_from, payload.depart_time_to,
                         payload.seats_needed, payload.group_size, payload.expected_price),
                    )
                    for tag in payload.tags:
                        cursor.execute(
                            "INSERT INTO order_tag (id, order_id, tag_content) VALUES (%s,%s,%s)",
                            (str(uuid.uuid4()), oid, tag),
                        )
                    cursor.execute(
                        """INSERT INTO order_passenger
                           (id, order_id, passenger_id, join_time, pay_status)
                           VALUES (%s,%s,%s,NOW(),'pending')""",
                        (str(uuid.uuid4()), oid, user_id),
                    )
                    return {"order_id": oid, "status": "published", "created_at": _now()}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    # Mock
    oid = _new_id()
    now = _now()
    _ORDERS[oid] = {
        "order_id": oid,
        "passenger_id": user_id,
        "start_loc": payload.start_loc,
        "end_loc": payload.end_loc,
        "depart_time_from": payload.depart_time_from,
        "depart_time_to": payload.depart_time_to,
        "seats_needed": payload.seats_needed,
        "seats_joined": payload.group_size,   # 发单方人数作为初始值
        "expected_price": payload.expected_price,
        "owner_id": None,
        "vehicle_id": None,
        "locked_time": None,
        "status": "published",
        "created_at": now,
        "updated_at": now,
    }
    _mock_set_tags(oid, payload.tags)
    rid = _new_id()
    _PASSENGERS[rid] = {
        "record_id": rid, "order_id": oid,
        "passenger_id": user_id, "join_time": now, "pay_status": "pending",
    }
    return {"order_id": oid, "status": "published", "created_at": now}


# ── 2. 搜索订单 ────────────────────────────────────────────────────────────────

def search_orders(
    start_loc: Optional[str],
    end_loc: Optional[str],
    time_from: Optional[str],
    time_to: Optional[str],
    tags: Optional[List[str]] = None,
) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    sql = "SELECT * FROM orders WHERE status IN ('published','full')"
                    params: list = []
                    if start_loc:
                        sql += " AND start_loc LIKE %s"
                        params.append(f"%{start_loc}%")
                    if end_loc:
                        sql += " AND end_loc LIKE %s"
                        params.append(f"%{end_loc}%")
                    if time_from:
                        sql += " AND depart_time_from >= %s"
                        params.append(time_from)
                    if time_to:
                        sql += " AND depart_time_to <= %s"
                        params.append(time_to)
                    if tags:
                        placeholders = ",".join(["%s"] * len(tags))
                        sql += (
                            f" AND EXISTS (SELECT 1 FROM order_tag"
                            f" WHERE order_tag.order_id = orders.id"
                            f" AND order_tag.tag_content IN ({placeholders}))"
                        )
                        params.extend(tags)
                    sql += " ORDER BY depart_time_from ASC LIMIT 50"
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                    items = [_db_format(r, _db_get_tags(cursor, r["id"])) for r in rows]
                    return {"items": items}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    # Mock
    items = []
    for o in _ORDERS.values():
        if o["status"] not in ("published", "full"):
            continue
        if start_loc and start_loc.lower() not in o["start_loc"].lower():
            continue
        if end_loc and end_loc.lower() not in o["end_loc"].lower():
            continue
        if time_from and o["depart_time_to"] < time_from:
            continue
        if time_to and o["depart_time_from"] > time_to:
            continue
        if tags:
            order_tags = _mock_get_tags(o["order_id"])
            if not any(t in order_tags for t in tags):
                continue
        items.append(_mock_format(o))
    items.sort(key=lambda x: x["depart_time_from"])
    return {"items": items}


# ── 3. 按用户列出订单 ──────────────────────────────────────────────────────────

def list_orders(passenger_id: Optional[str], owner_id: Optional[str]) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    if passenger_id:
                        cursor.execute(
                            """SELECT DISTINCT o.* FROM orders o
                               LEFT JOIN order_passenger op ON o.id = op.order_id
                               WHERE o.passenger_id = %s OR op.passenger_id = %s
                               ORDER BY o.created_at DESC""",
                            (passenger_id, passenger_id),
                        )
                    elif owner_id:
                        cursor.execute(
                            "SELECT * FROM orders WHERE owner_id = %s ORDER BY locked_time DESC",
                            (owner_id,),
                        )
                    else:
                        cursor.execute(
                            "SELECT * FROM orders ORDER BY created_at DESC LIMIT 200"
                        )
                    rows = cursor.fetchall()
                    items = [_db_format(r, _db_get_tags(cursor, r["id"])) for r in rows]
                    return {"items": items}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    # Mock
    if passenger_id:
        participated = {p["order_id"] for p in _PASSENGERS.values()
                        if p["passenger_id"] == passenger_id}
        published_ids = {o["order_id"] for o in _ORDERS.values()
                         if o["passenger_id"] == passenger_id}
        all_ids = participated | published_ids
        items = [_mock_format(_ORDERS[oid]) for oid in all_ids if oid in _ORDERS]
    elif owner_id:
        items = [_mock_format(o) for o in _ORDERS.values() if o["owner_id"] == owner_id]
    else:
        items = [_mock_format(o) for o in _ORDERS.values()]

    items.sort(key=lambda x: x["created_at"], reverse=True)
    return {"items": items}


# ── 4. 订单详情 ────────────────────────────────────────────────────────────────

def get_order_detail(order_id: str) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
                    row = cursor.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Order not found")
                    tags = _db_get_tags(cursor, order_id)
                    return _db_format(row, tags)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    o = _ORDERS.get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return _mock_format(o)


# ── 5. 修改订单（仅 published 状态） ──────────────────────────────────────────

def update_order(order_id: str, payload: OrderUpdateRequest, user_id: str) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
                    row = cursor.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Order not found")
                    if row["status"] != "published":
                        raise HTTPException(status_code=409, detail="Only published orders can be updated")
                    if row["passenger_id"] != user_id:
                        raise HTTPException(status_code=403, detail="Not authorized")

                    sets, params = [], []
                    if payload.start_loc is not None:
                        sets.append("start_loc = %s"); params.append(payload.start_loc)
                    if payload.end_loc is not None:
                        sets.append("end_loc = %s"); params.append(payload.end_loc)
                    if payload.depart_time_from is not None:
                        sets.append("depart_time_from = %s"); params.append(payload.depart_time_from)
                    if payload.depart_time_to is not None:
                        sets.append("depart_time_to = %s"); params.append(payload.depart_time_to)
                    if payload.seats_needed is not None:
                        sets.append("seats_needed = %s"); params.append(payload.seats_needed)
                    if payload.expected_price is not None:
                        sets.append("expected_price = %s"); params.append(payload.expected_price)
                    sets.append("updated_at = NOW()")
                    params.append(order_id)

                    if sets:
                        cursor.execute(
                            f"UPDATE orders SET {', '.join(sets)} WHERE id = %s", params
                        )
                    if payload.tags is not None:
                        cursor.execute("DELETE FROM order_tag WHERE order_id = %s", (order_id,))
                        for tag in payload.tags:
                            cursor.execute(
                                "INSERT INTO order_tag (id, order_id, tag_content) VALUES (%s,%s,%s)",
                                (str(uuid.uuid4()), order_id, tag),
                            )
                    return {"order_id": order_id, "updated_at": _now()}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    o = _ORDERS.get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    if o["status"] != "published":
        raise HTTPException(status_code=409, detail="Only published orders can be updated")
    if o["passenger_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if payload.start_loc is not None:        o["start_loc"] = payload.start_loc
    if payload.end_loc is not None:          o["end_loc"] = payload.end_loc
    if payload.depart_time_from is not None: o["depart_time_from"] = payload.depart_time_from
    if payload.depart_time_to is not None:   o["depart_time_to"] = payload.depart_time_to
    if payload.seats_needed is not None:     o["seats_needed"] = payload.seats_needed
    if payload.expected_price is not None:   o["expected_price"] = payload.expected_price
    if payload.tags is not None:             _mock_set_tags(order_id, payload.tags)
    o["updated_at"] = _now()
    return {"order_id": order_id, "updated_at": o["updated_at"]}


# ── 6. 取消订单 ────────────────────────────────────────────────────────────────

def cancel_order(order_id: str, user_id: str, is_admin: bool = False) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
                    row = cursor.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Order not found")
                    if row["status"] in ("completed", "cancelled"):
                        raise HTTPException(status_code=409, detail="Order already ended")

                    is_publisher = row["passenger_id"] == user_id
                    is_owner = row["owner_id"] == user_id
                    if not is_admin and not is_publisher and not is_owner:
                        cursor.execute(
                            "SELECT id FROM order_passenger WHERE order_id=%s AND passenger_id=%s",
                            (order_id, user_id),
                        )
                        if not cursor.fetchone():
                            raise HTTPException(status_code=403, detail="Not authorized")

                    needs_penalty = row["status"] in ("locked", "full")
                    cursor.execute(
                        "UPDATE orders SET status='cancelled', updated_at=NOW() WHERE id=%s",
                        (order_id,),
                    )
                    return {"order_id": order_id, "status": "cancelled", "penalty": needs_penalty}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    o = _ORDERS.get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    if o["status"] in ("completed", "cancelled"):
        raise HTTPException(status_code=409, detail="Order already ended")

    is_publisher = o["passenger_id"] == user_id
    is_owner = o["owner_id"] == user_id
    if not is_admin and not is_publisher and not is_owner:
        has_joined = any(
            p["passenger_id"] == user_id and p["order_id"] == order_id
            for p in _PASSENGERS.values()
        )
        if not has_joined:
            raise HTTPException(status_code=403, detail="Not authorized")

    needs_penalty = o["status"] in ("locked", "full")
    o["status"] = "cancelled"
    o["updated_at"] = _now()
    return {"order_id": order_id, "status": "cancelled", "penalty": needs_penalty}


# ── 7. 拼车人加入订单 ──────────────────────────────────────────────────────────

def join_order(order_id: str, user_id: str) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM orders WHERE id = %s FOR UPDATE", (order_id,))
                    row = cursor.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Order not found")
                    if row["status"] != "published":
                        raise HTTPException(status_code=409, detail="Order is not accepting passengers")
                    if row["seats_joined"] >= row["seats_needed"]:
                        raise HTTPException(status_code=409, detail="Order is full")
                    cursor.execute(
                        "SELECT id FROM order_passenger WHERE order_id=%s AND passenger_id=%s",
                        (order_id, user_id),
                    )
                    if cursor.fetchone():
                        raise HTTPException(status_code=409, detail="Already joined this order")

                    cursor.execute(
                        """INSERT INTO order_passenger (id, order_id, passenger_id, join_time, pay_status)
                           VALUES (%s,%s,%s,NOW(),'pending')""",
                        (str(uuid.uuid4()), order_id, user_id),
                    )
                    new_joined = row["seats_joined"] + 1
                    new_status = "full" if new_joined >= row["seats_needed"] else "published"
                    cursor.execute(
                        "UPDATE orders SET seats_joined=%s, status=%s, updated_at=NOW() WHERE id=%s",
                        (new_joined, new_status, order_id),
                    )
                    return {
                        "order_id": order_id,
                        "status": new_status,
                        "seats_joined": new_joined,
                        "remaining_seats": max(0, row["seats_needed"] - new_joined),
                    }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    o = _ORDERS.get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    if o["status"] != "published":
        raise HTTPException(status_code=409, detail="Order is not accepting passengers")
    if o["seats_joined"] >= o["seats_needed"]:
        raise HTTPException(status_code=409, detail="Order is full")
    if any(p["passenger_id"] == user_id and p["order_id"] == order_id for p in _PASSENGERS.values()):
        raise HTTPException(status_code=409, detail="Already joined this order")

    rid = _new_id()
    _PASSENGERS[rid] = {
        "record_id": rid, "order_id": order_id,
        "passenger_id": user_id, "join_time": _now(), "pay_status": "pending",
    }
    o["seats_joined"] += 1
    if o["seats_joined"] >= o["seats_needed"]:
        o["status"] = "full"
    o["updated_at"] = _now()
    return {
        "order_id": order_id,
        "status": o["status"],
        "seats_joined": o["seats_joined"],
        "remaining_seats": max(0, o["seats_needed"] - o["seats_joined"]),
    }


# ── 8. 车主接单 ────────────────────────────────────────────────────────────────

def accept_order(order_id: str, payload: AcceptOrderRequest, user_id: str) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
                    row = cursor.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Order not found")
                    if row["status"] not in ("published", "full"):
                        raise HTTPException(status_code=409, detail="Order cannot be accepted")

                    locked_time = datetime.now()
                    cursor.execute(
                        """UPDATE orders SET owner_id=%s, vehicle_id=%s,
                           locked_time=%s, status='locked', updated_at=NOW() WHERE id=%s""",
                        (user_id, payload.vehicle_id, locked_time, order_id),
                    )
                    return {
                        "order_id": order_id,
                        "status": "locked",
                        "locked_time": locked_time.isoformat(timespec="seconds"),
                    }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    o = _ORDERS.get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    if o["status"] not in ("published", "full"):
        raise HTTPException(status_code=409, detail="Order cannot be accepted")

    locked_time = _now()
    o["owner_id"] = user_id
    o["vehicle_id"] = payload.vehicle_id
    o["locked_time"] = locked_time
    o["status"] = "locked"
    o["updated_at"] = locked_time
    return {"order_id": order_id, "status": "locked", "locked_time": locked_time}


# ── 9. 标记完成（域3支付成功后回调） ──────────────────────────────────────────

def complete_order(order_id: str) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
                    row = cursor.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Order not found")
                    if row["status"] != "locked":
                        raise HTTPException(status_code=409, detail="Order must be in locked status to complete")
                    cursor.execute(
                        "UPDATE orders SET status='completed', updated_at=NOW() WHERE id=%s",
                        (order_id,),
                    )
                    return {"order_id": order_id, "status": "completed"}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    o = _ORDERS.get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    if o["status"] != "locked":
        raise HTTPException(status_code=409, detail="Order must be in locked status to complete")
    o["status"] = "completed"
    o["updated_at"] = _now()
    return {"order_id": order_id, "status": "completed"}


# ── 10. 查询车主名下车辆 ────────────────────────────────────────────────────────

def list_vehicles(owner_id: str) -> dict:
    """返回该车主名下所有可用车辆（available 状态）"""
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT id AS vehicle_id, owner_user_id AS owner_id,
                                  plate_no, brand, color, seat_capacity, status
                           FROM vehicle
                           WHERE owner_user_id = %s AND status = 'available'
                           ORDER BY created_at DESC""",
                        (owner_id,),
                    )
                    rows = cursor.fetchall()
                    vehicles = [
                        {
                            "vehicle_id": str(r["vehicle_id"]),
                            "owner_id": str(r["owner_id"]),
                            "plate_no": r["plate_no"],
                            "brand": r["brand"] or "",
                            "color": r["color"] or "",
                            "seat_capacity": r["seat_capacity"],
                            "status": r["status"],
                        }
                        for r in rows
                    ]
                    return {"vehicles": vehicles}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    # Mock
    vehicles = [
        v for v in _VEHICLES.values()
        if v["owner_id"] == owner_id and v["status"] == "available"
    ]
    # dev 兜底：若该 userId 名下无车，返回全部可用 mock 车辆（方便演示）
    if not vehicles:
        vehicles = [v for v in _VEHICLES.values() if v["status"] == "available"]
    return {"vehicles": vehicles}
