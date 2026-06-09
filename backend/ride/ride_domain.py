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
  7.  POST   /api/orders/{id}/join    乘客加入
  8.  POST   /api/orders/{id}/accept  车主接单
  9.  POST   /api/orders/{id}/complete 标记完成（域3回调）
  10. GET    /api/orders/all          管理员查看全部订单（alias → list_orders 无参数）
"""
import re
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


class VehicleCreateRequest(BaseModel):
    owner_id: Optional[str] = None
    plate_no: str
    brand: str = ""
    color: str = ""
    seat_capacity: int = 4


class VehicleUpdateRequest(BaseModel):
    plate_no: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    seat_capacity: Optional[int] = None


class VehicleStatusUpdateRequest(BaseModel):
    status: str


class VehicleVerifyUpdateRequest(BaseModel):
    verified: bool


class VehicleVerifySubmitRequest(BaseModel):
    owner_name: str
    id_no: str
    driver_license_no: str
    vehicle_license_no: str
    contact_phone: str = ""
    remark: str = ""


class VehicleVerifyReviewRequest(BaseModel):
    decision: str
    review_note: str = ""


# ── Mock Data Store ───────────────────────────────────────────────────────────

def _new_id() -> str:
    return str(uuid.uuid4())[:12]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# 预置种子数据，方便开发调试
_ORDERS: dict = {
    "ord-seed-001": {
        "order_id": "ord-seed-001",
        "passenger_id": "3",
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
        "passenger_id": "2",
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
        "passenger_id": "3",
        "start_loc": "珠江新城",
        "end_loc": "广州白云机场",
        "depart_time_from": "2026-04-17T06:00:00",
        "depart_time_to": "2026-04-17T07:00:00",
        "seats_needed": 3,
        "seats_joined": 3,
        "expected_price": 80.00,
        "owner_id": "998",
        "vehicle_id": "veh-mock-001",
        "locked_time": "2026-04-13T12:00:00",
        "status": "locked",
        "created_at": "2026-04-13T08:00:00",
        "updated_at": "2026-04-13T12:00:00",
    },
    "ord-seed-004": {
        "order_id": "ord-seed-004",
        "passenger_id": "2",
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
        "passenger_id": "3", "join_time": "2026-04-13T10:00:00",
        "pay_status": "pending",
    },
    "rec-s2": {
        "record_id": "rec-s2", "order_id": "ord-seed-002",
        "passenger_id": "2", "join_time": "2026-04-13T09:00:00",
        "pay_status": "pending",
    },
    "rec-s3": {
        "record_id": "rec-s3", "order_id": "ord-seed-003",
        "passenger_id": "3", "join_time": "2026-04-13T08:00:00",
        "pay_status": "pending",
    },
    "rec-s4": {
        "record_id": "rec-s4", "order_id": "ord-seed-003",
        "passenger_id": "2", "join_time": "2026-04-13T08:30:00",
        "pay_status": "pending",
    },
    "rec-s5": {
        "record_id": "rec-s5", "order_id": "ord-seed-003",
        "passenger_id": "998", "join_time": "2026-04-13T09:00:00",
        "pay_status": "pending",
    },
}


# 车辆 mock 数据（dev 环境，与账号 mock 用户 yxx/driver1 对齐）
_VEHICLES: dict = {
    "veh-mock-001": {
        "vehicle_id": "veh-mock-001",
        "owner_id": "998",
        "plate_no": "粤A·88888",
        "brand": "丰田 凯美瑞",
        "color": "珍珠白",
        "seat_capacity": 5,
        "verified": True,
        "status": "available",
    },
    "veh-mock-002": {
        "vehicle_id": "veh-mock-002",
        "owner_id": "2",
        "plate_no": "粤B·12345",
        "brand": "本田 雅阁",
        "color": "深空黑",
        "seat_capacity": 5,
        "verified": True,
        "status": "available",
    },
    "veh-mock-003": {
        "vehicle_id": "veh-mock-003",
        "owner_id": "2",
        "plate_no": "粤C·67890",
        "brand": "大众 帕萨特",
        "color": "银色",
        "seat_capacity": 5,
        "verified": True,
        "status": "available",
    },
}

_VEHICLE_VERIFY_REQUESTS: dict = {}

ALLOWED_VEHICLE_STATUS = {"available", "disabled"}
ALLOWED_VERIFY_REQUEST_STATUS = {"pending", "approved", "rejected"}
PLATE_NO_PATTERN = re.compile(
    r"^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-HJ-NP-Z0-9]{5,6}$"
)


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


def _mock_get_passengers(order_id: str) -> List[dict]:
    rows = [
        p for p in _PASSENGERS.values()
        if p["order_id"] == order_id
    ]
    rows.sort(key=lambda p: p["join_time"])
    return [
        {
            "record_id": p["record_id"],
            "order_id": p["order_id"],
            "passenger_id": p["passenger_id"],
            "join_time": p["join_time"],
            "pay_status": p["pay_status"],
        }
        for p in rows
    ]


# ── DB Helpers ────────────────────────────────────────────────────────────────

def _db_get_tags(cursor, order_id: str) -> List[str]:
    cursor.execute("SELECT tag_content FROM order_tag WHERE order_id = %s", (order_id,))
    return [row["tag_content"] for row in cursor.fetchall()]


def _db_get_passengers(cursor, order_id: str) -> List[dict]:
    cursor.execute(
        """SELECT id, order_id, passenger_id, join_time, pay_status
           FROM order_passenger
           WHERE order_id = %s
           ORDER BY join_time ASC""",
        (order_id,),
    )
    return [
        {
            "record_id": row["id"],
            "order_id": row["order_id"],
            "passenger_id": row["passenger_id"],
            "join_time": _iso(row["join_time"]),
            "pay_status": row["pay_status"],
        }
        for row in cursor.fetchall()
    ]


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


def _normalize_plate_no(plate_no: str) -> str:
    plate_no_pattern = re.compile(
        "^[\u4EAC\u6D25\u6CAA\u6E1D\u5180\u8C6B\u4E91\u8FBD\u9ED1\u6E58\u7696\u9C81"
        "\u65B0\u82CF\u6D59\u8D63\u9102\u6842\u7518\u664B\u8499\u9655\u5409\u95FD\u8D35"
        "\u7CA4\u9752\u85CF\u5DDD\u5B81\u743C\u4F7F\u9886][A-Z][A-HJ-NP-Z0-9]{5,6}$"
    )
    normalized = (plate_no or "").strip().upper()
    normalized = re.sub(r"[\s\-·•.]", "", normalized)
    if not normalized:
        raise HTTPException(status_code=400, detail="plate_no cannot be empty")
    if not plate_no_pattern.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="plate_no format is invalid")
    return normalized


def _validate_seat_capacity(seat_capacity: int) -> None:
    if seat_capacity < 2 or seat_capacity > 9:
        raise HTTPException(
            status_code=400,
            detail="seat_capacity must be between 2 and 9",
        )


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off", ""}:
            return False
    return bool(value)


def _format_vehicle(row: dict) -> dict:
    verified = _as_bool(row.get("verified", False))
    verify_status = row.get("verify_status") or ("approved" if verified else "unsubmitted")
    item = {
        "vehicle_id": str(row["vehicle_id"]),
        "owner_id": str(row["owner_id"]),
        "plate_no": row["plate_no"],
        "brand": row.get("brand") or "",
        "color": row.get("color") or "",
        "seat_capacity": int(row["seat_capacity"]),
        "verified": verified,
        "verify_status": verify_status,
        "status": row["status"],
    }
    if row.get("pending_request_id") is not None:
        item["pending_request_id"] = str(row["pending_request_id"])
    return item


def _format_vehicle_verify_request(row: dict) -> dict:
    return {
        "request_id": str(row["request_id"]),
        "vehicle_id": str(row["vehicle_id"]),
        "owner_user_id": str(row["owner_user_id"]),
        "owner_name": row["owner_name"],
        "id_no": row["id_no"],
        "driver_license_no": row["driver_license_no"],
        "vehicle_license_no": row["vehicle_license_no"],
        "contact_phone": row.get("contact_phone") or "",
        "remark": row.get("remark") or "",
        "status": row["status"],
        "review_note": row.get("review_note") or "",
        "reviewed_by": row.get("reviewed_by"),
        "reviewed_at": _iso(row.get("reviewed_at")),
        "created_at": _iso(row.get("created_at")),
        "vehicle": row.get("vehicle"),
    }


def _mask_id_no(id_no: str) -> str:
    text = (id_no or "").strip()
    if len(text) <= 8:
        return text
    return f"{text[:4]}****{text[-4:]}"


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
                    detail = _db_format(row, tags)
                    detail["passengers"] = _db_get_passengers(cursor, order_id)
                    return detail
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    o = _ORDERS.get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    detail = _mock_format(o)
    detail["passengers"] = _mock_get_passengers(order_id)
    return detail


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


# ── 7. 乘客加入订单 ──────────────────────────────────────────────────────────

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
                    cursor.execute(
                        """SELECT id FROM vehicle
                           WHERE id=%s AND owner_user_id=%s
                             AND status='available' AND verified=1""",
                        (payload.vehicle_id, user_id),
                    )
                    if not cursor.fetchone():
                        raise HTTPException(
                            status_code=403,
                            detail="No verified available vehicle for this owner",
                        )

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
    vehicle = _VEHICLES.get(payload.vehicle_id)
    if not vehicle or vehicle["owner_id"] != user_id:
        raise HTTPException(status_code=403, detail="No vehicle for this owner")
    if vehicle["status"] != "available" or not _as_bool(vehicle.get("verified", False)):
        raise HTTPException(status_code=403, detail="No verified available vehicle for this owner")

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
    """返回该车主名下车辆。"""
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT v.id AS vehicle_id, v.owner_user_id AS owner_id,
                                  v.plate_no, v.brand, v.color, v.seat_capacity,
                                  v.verified, v.status,
                                  CASE
                                    WHEN v.verified=1 THEN 'approved'
                                    WHEN EXISTS (
                                      SELECT 1 FROM vehicle_verify_request r
                                      WHERE r.vehicle_id=v.id AND r.status='pending'
                                    ) THEN 'pending'
                                    ELSE 'unsubmitted'
                                  END AS verify_status,
                                  (
                                    SELECT r.id FROM vehicle_verify_request r
                                    WHERE r.vehicle_id=v.id AND r.status='pending'
                                    ORDER BY r.created_at DESC
                                    LIMIT 1
                                  ) AS pending_request_id
                           FROM vehicle v
                           WHERE v.owner_user_id = %s
                           ORDER BY v.created_at DESC""",
                        (owner_id,),
                    )
                    rows = cursor.fetchall()
                    return {"items": [_format_vehicle(r) for r in rows]}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    vehicles = []
    for vehicle in _VEHICLES.values():
        if vehicle["owner_id"] != owner_id:
            continue
        item = dict(vehicle)
        has_pending_request = any(
            req["vehicle_id"] == vehicle["vehicle_id"] and req["status"] == "pending"
            for req in _VEHICLE_VERIFY_REQUESTS.values()
        )
        pending_request = next(
            (
                req for req in _VEHICLE_VERIFY_REQUESTS.values()
                if req["vehicle_id"] == vehicle["vehicle_id"] and req["status"] == "pending"
            ),
            None,
        )
        item["verify_status"] = (
            "approved"
            if _as_bool(item.get("verified", False))
            else "pending" if has_pending_request else "unsubmitted"
        )
        if pending_request:
            item["pending_request_id"] = pending_request["request_id"]
        vehicles.append(item)
    return {"items": vehicles}


def create_vehicle(payload: VehicleCreateRequest, owner_id: Optional[str] = None) -> dict:
    plate_no = _normalize_plate_no(payload.plate_no)
    _validate_seat_capacity(payload.seat_capacity)
    resolved_owner_id = owner_id or payload.owner_id
    if not resolved_owner_id:
        raise HTTPException(status_code=400, detail="owner_id is required")

    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM vehicle WHERE plate_no=%s", (plate_no,))
                    if cursor.fetchone():
                        raise HTTPException(status_code=409, detail="plate_no already exists")
                    cursor.execute(
                        """INSERT INTO vehicle
                           (owner_user_id, plate_no, brand, color, seat_capacity, status)
                           VALUES (%s, %s, %s, %s, %s, 'available')""",
                        (
                            resolved_owner_id,
                            plate_no,
                            payload.brand,
                            payload.color,
                            payload.seat_capacity,
                        ),
                    )
                    vehicle_id = str(cursor.lastrowid)
                    return {
                        "message": "vehicle created",
                        "vehicle_id": vehicle_id,
                        "status": "available",
                    }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    if any(v["plate_no"] == plate_no for v in _VEHICLES.values()):
        raise HTTPException(status_code=409, detail="plate_no already exists")
    vehicle_id = f"veh-mock-{_new_id()}"
    _VEHICLES[vehicle_id] = {
        "vehicle_id": vehicle_id,
        "owner_id": resolved_owner_id,
        "plate_no": plate_no,
        "brand": payload.brand,
        "color": payload.color,
        "seat_capacity": payload.seat_capacity,
        "verified": False,
        "status": "available",
    }
    return {"message": "vehicle created", "vehicle_id": vehicle_id, "status": "available"}


def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdateRequest,
    owner_id: Optional[str] = None,
) -> dict:
    has_changes = any(
        value is not None
        for value in (payload.plate_no, payload.brand, payload.color, payload.seat_capacity)
    )
    if not has_changes:
        raise HTTPException(status_code=400, detail="no fields to update")

    normalized_plate = _normalize_plate_no(payload.plate_no) if payload.plate_no is not None else None
    if payload.seat_capacity is not None:
        _validate_seat_capacity(payload.seat_capacity)

    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT id AS vehicle_id, owner_user_id AS owner_id,
                                  plate_no, brand, color, seat_capacity, verified, status
                           FROM vehicle WHERE id=%s""",
                        (vehicle_id,),
                    )
                    existing = cursor.fetchone()
                    if not existing:
                        raise HTTPException(status_code=404, detail="vehicle not found")
                    if owner_id is not None and str(existing["owner_id"]) != str(owner_id):
                        raise HTTPException(status_code=403, detail="no permission for this vehicle")
                    if normalized_plate and normalized_plate != existing["plate_no"]:
                        cursor.execute("SELECT id FROM vehicle WHERE plate_no=%s", (normalized_plate,))
                        if cursor.fetchone():
                            raise HTTPException(status_code=409, detail="plate_no already exists")

                    updates = []
                    values = []
                    if normalized_plate is not None:
                        updates.append("plate_no=%s")
                        values.append(normalized_plate)
                    if payload.brand is not None:
                        updates.append("brand=%s")
                        values.append(payload.brand)
                    if payload.color is not None:
                        updates.append("color=%s")
                        values.append(payload.color)
                    if payload.seat_capacity is not None:
                        updates.append("seat_capacity=%s")
                        values.append(payload.seat_capacity)
                    values.append(vehicle_id)
                    cursor.execute(f"UPDATE vehicle SET {', '.join(updates)} WHERE id=%s", tuple(values))
                    cursor.execute(
                        """SELECT id AS vehicle_id, owner_user_id AS owner_id,
                                  plate_no, brand, color, seat_capacity, verified, status
                           FROM vehicle WHERE id=%s""",
                        (vehicle_id,),
                    )
                    updated = cursor.fetchone()
                    return {"message": "vehicle updated", "vehicle": _format_vehicle(updated)}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    vehicle = _VEHICLES.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")
    if owner_id is not None and str(vehicle["owner_id"]) != str(owner_id):
        raise HTTPException(status_code=403, detail="no permission for this vehicle")
    if normalized_plate and normalized_plate != vehicle["plate_no"]:
        duplicate = any(
            v["plate_no"] == normalized_plate and v["vehicle_id"] != vehicle_id
            for v in _VEHICLES.values()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="plate_no already exists")
        vehicle["plate_no"] = normalized_plate
    if payload.brand is not None:
        vehicle["brand"] = payload.brand
    if payload.color is not None:
        vehicle["color"] = payload.color
    if payload.seat_capacity is not None:
        vehicle["seat_capacity"] = payload.seat_capacity
    return {"message": "vehicle updated", "vehicle": dict(vehicle)}


def update_vehicle_status(
    vehicle_id: str,
    payload: VehicleStatusUpdateRequest,
    owner_id: Optional[str] = None,
) -> dict:
    next_status = (payload.status or "").strip().lower()
    if next_status not in ALLOWED_VEHICLE_STATUS:
        raise HTTPException(status_code=400, detail="status must be one of: available, disabled")

    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, owner_user_id AS owner_id FROM vehicle WHERE id=%s",
                        (vehicle_id,),
                    )
                    vehicle = cursor.fetchone()
                    if not vehicle:
                        raise HTTPException(status_code=404, detail="vehicle not found")
                    if owner_id is not None and str(vehicle["owner_id"]) != str(owner_id):
                        raise HTTPException(status_code=403, detail="no permission for this vehicle")
                    cursor.execute("UPDATE vehicle SET status=%s WHERE id=%s", (next_status, vehicle_id))
                    return {
                        "message": "vehicle status updated",
                        "vehicle_id": vehicle_id,
                        "status": next_status,
                    }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    vehicle = _VEHICLES.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")
    if owner_id is not None and str(vehicle["owner_id"]) != str(owner_id):
        raise HTTPException(status_code=403, detail="no permission for this vehicle")
    vehicle["status"] = next_status
    return {"message": "vehicle status updated", "vehicle_id": vehicle_id, "status": next_status}


def update_vehicle_verified(vehicle_id: str, payload: VehicleVerifyUpdateRequest) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM vehicle WHERE id=%s", (vehicle_id,))
                    if not cursor.fetchone():
                        raise HTTPException(status_code=404, detail="vehicle not found")
                    cursor.execute(
                        "UPDATE vehicle SET verified=%s WHERE id=%s",
                        (1 if payload.verified else 0, vehicle_id),
                    )
                    return {
                        "message": "vehicle verification updated",
                        "vehicle_id": vehicle_id,
                        "verified": payload.verified,
                    }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    vehicle = _VEHICLES.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")
    vehicle["verified"] = payload.verified
    return {"message": "vehicle verification updated", "vehicle_id": vehicle_id, "verified": payload.verified}


def submit_vehicle_verify_request(
    vehicle_id: str,
    payload: VehicleVerifySubmitRequest,
    owner_id: str,
) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, owner_user_id, verified FROM vehicle WHERE id=%s",
                        (vehicle_id,),
                    )
                    vehicle = cursor.fetchone()
                    if not vehicle:
                        raise HTTPException(status_code=404, detail="vehicle not found")
                    if str(vehicle["owner_user_id"]) != str(owner_id):
                        raise HTTPException(status_code=403, detail="no permission for this vehicle")
                    if _as_bool(vehicle.get("verified", 0)):
                        raise HTTPException(status_code=409, detail="vehicle already verified")
                    cursor.execute(
                        """SELECT id FROM vehicle_verify_request
                           WHERE vehicle_id=%s AND status='pending' LIMIT 1""",
                        (vehicle_id,),
                    )
                    if cursor.fetchone():
                        raise HTTPException(status_code=409, detail="verification request already pending")
                    cursor.execute(
                        """INSERT INTO vehicle_verify_request
                           (vehicle_id, owner_user_id, owner_name, id_no,
                            driver_license_no, vehicle_license_no, contact_phone, remark, status)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')""",
                        (
                            vehicle_id,
                            owner_id,
                            payload.owner_name,
                            payload.id_no,
                            payload.driver_license_no,
                            payload.vehicle_license_no,
                            payload.contact_phone,
                            payload.remark,
                        ),
                    )
                    request_id = str(cursor.lastrowid)
                    return {
                        "message": "vehicle verification request submitted",
                        "request_id": request_id,
                        "vehicle_id": vehicle_id,
                        "status": "pending",
                    }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    vehicle = _VEHICLES.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")
    if vehicle["owner_id"] != owner_id:
        raise HTTPException(status_code=403, detail="no permission for this vehicle")
    if _as_bool(vehicle.get("verified", False)):
        raise HTTPException(status_code=409, detail="vehicle already verified")
    if any(
        req["vehicle_id"] == vehicle_id and req["status"] == "pending"
        for req in _VEHICLE_VERIFY_REQUESTS.values()
    ):
        raise HTTPException(status_code=409, detail="verification request already pending")

    request_id = f"verify-{_new_id()}"
    _VEHICLE_VERIFY_REQUESTS[request_id] = {
        "request_id": request_id,
        "vehicle_id": vehicle_id,
        "owner_user_id": owner_id,
        "owner_name": payload.owner_name,
        "id_no": payload.id_no,
        "driver_license_no": payload.driver_license_no,
        "vehicle_license_no": payload.vehicle_license_no,
        "contact_phone": payload.contact_phone,
        "remark": payload.remark,
        "status": "pending",
        "review_note": "",
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": _now(),
        "vehicle": dict(vehicle),
    }
    return {
        "message": "vehicle verification request submitted",
        "request_id": request_id,
        "vehicle_id": vehicle_id,
        "status": "pending",
    }


def withdraw_vehicle_verify_request(request_id: str, owner_id: str) -> dict:
    """Withdraw a pending vehicle verification request and remove its unverified vehicle."""
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT r.id, r.vehicle_id, r.owner_user_id, r.status,
                                  v.verified
                           FROM vehicle_verify_request r
                           JOIN vehicle v ON v.id = r.vehicle_id
                           WHERE r.id=%s""",
                        (request_id,),
                    )
                    request = cursor.fetchone()
                    if not request:
                        raise HTTPException(status_code=404, detail="verification request not found")
                    if str(request["owner_user_id"]) != str(owner_id):
                        raise HTTPException(status_code=403, detail="no permission for this request")
                    if request["status"] != "pending":
                        raise HTTPException(status_code=409, detail="only pending request can be withdrawn")
                    if _as_bool(request.get("verified", 0)):
                        raise HTTPException(status_code=409, detail="verified vehicle cannot be withdrawn")

                    cursor.execute("DELETE FROM vehicle_verify_request WHERE id=%s", (request_id,))
                    cursor.execute("DELETE FROM vehicle WHERE id=%s AND verified=0", (request["vehicle_id"],))
                    return {
                        "message": "vehicle verification request withdrawn",
                        "request_id": str(request_id),
                        "vehicle_id": str(request["vehicle_id"]),
                    }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    request = _VEHICLE_VERIFY_REQUESTS.get(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="verification request not found")
    if str(request["owner_user_id"]) != str(owner_id):
        raise HTTPException(status_code=403, detail="no permission for this request")
    if request["status"] != "pending":
        raise HTTPException(status_code=409, detail="only pending request can be withdrawn")

    vehicle_id = request["vehicle_id"]
    vehicle = _VEHICLES.get(vehicle_id)
    if vehicle and _as_bool(vehicle.get("verified", False)):
        raise HTTPException(status_code=409, detail="verified vehicle cannot be withdrawn")

    del _VEHICLE_VERIFY_REQUESTS[request_id]
    if vehicle_id in _VEHICLES:
        del _VEHICLES[vehicle_id]
    return {
        "message": "vehicle verification request withdrawn",
        "request_id": request_id,
        "vehicle_id": vehicle_id,
    }


def list_vehicle_verify_requests(status: Optional[str] = "pending") -> dict:
    normalized_status = (status or "").strip().lower() or None
    if normalized_status and normalized_status not in ALLOWED_VERIFY_REQUEST_STATUS:
        raise HTTPException(status_code=400, detail="status must be one of: pending, approved, rejected")
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    sql = (
                        """SELECT r.id AS request_id, r.vehicle_id, r.owner_user_id,
                                  r.owner_name, r.id_no, r.driver_license_no,
                                  r.vehicle_license_no, r.contact_phone, r.remark,
                                  r.status, r.review_note, r.reviewed_by,
                                  r.reviewed_at, r.created_at,
                                  v.plate_no, v.brand, v.color, v.seat_capacity,
                                  v.verified, v.status AS vehicle_status
                           FROM vehicle_verify_request r
                           JOIN vehicle v ON v.id = r.vehicle_id """
                    )
                    params = []
                    if normalized_status:
                        sql += "WHERE r.status=%s "
                        params.append(normalized_status)
                    sql += "ORDER BY r.created_at DESC"
                    cursor.execute(sql, tuple(params))
                    items = []
                    for row in cursor.fetchall():
                        item = _format_vehicle_verify_request(
                            {
                                **row,
                                "vehicle": {
                                    "plate_no": row.get("plate_no") or "",
                                    "brand": row.get("brand") or "",
                                    "color": row.get("color") or "",
                                    "seat_capacity": int(row.get("seat_capacity") or 0),
                                    "verified": _as_bool(row.get("verified", 0)),
                                    "status": row.get("vehicle_status") or "",
                                },
                            }
                        )
                        item["id_no_masked"] = _mask_id_no(item["id_no"])
                        items.append(item)
                    return {"items": items}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    items = []
    for row in _VEHICLE_VERIFY_REQUESTS.values():
        if normalized_status and row["status"] != normalized_status:
            continue
        item = _format_vehicle_verify_request(row)
        item["id_no_masked"] = _mask_id_no(item["id_no"])
        items.append(item)
    items.sort(key=lambda item: item["created_at"], reverse=True)
    return {"items": items}


def review_vehicle_verify_request(
    request_id: str,
    payload: VehicleVerifyReviewRequest,
    reviewer_id: str,
) -> dict:
    decision = (payload.decision or "").strip().lower()
    if decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="decision must be approved or rejected")
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, vehicle_id, status FROM vehicle_verify_request WHERE id=%s",
                        (request_id,),
                    )
                    request = cursor.fetchone()
                    if not request:
                        raise HTTPException(status_code=404, detail="verification request not found")
                    if request["status"] != "pending":
                        raise HTTPException(status_code=409, detail="verification request already reviewed")
                    cursor.execute(
                        """UPDATE vehicle_verify_request
                           SET status=%s, review_note=%s, reviewed_by=%s, reviewed_at=%s
                           WHERE id=%s""",
                        (decision, payload.review_note, reviewer_id, datetime.now(), request_id),
                    )
                    if decision == "approved":
                        cursor.execute(
                            "UPDATE vehicle SET verified=1 WHERE id=%s",
                            (request["vehicle_id"],),
                        )
                    return {
                        "message": "vehicle verification request reviewed",
                        "request_id": request_id,
                        "decision": decision,
                    }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    request = _VEHICLE_VERIFY_REQUESTS.get(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="verification request not found")
    if request["status"] != "pending":
        raise HTTPException(status_code=409, detail="verification request already reviewed")
    request["status"] = decision
    request["review_note"] = payload.review_note
    request["reviewed_by"] = reviewer_id
    request["reviewed_at"] = _now()
    if decision == "approved" and request["vehicle_id"] in _VEHICLES:
        _VEHICLES[request["vehicle_id"]]["verified"] = True
    return {"message": "vehicle verification request reviewed", "request_id": request_id, "decision": decision}


def delete_vehicle(vehicle_id: str, owner_id: Optional[str] = None) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, owner_user_id AS owner_id FROM vehicle WHERE id=%s",
                        (vehicle_id,),
                    )
                    vehicle = cursor.fetchone()
                    if not vehicle:
                        raise HTTPException(status_code=404, detail="vehicle not found")
                    if owner_id is not None and str(vehicle["owner_id"]) != str(owner_id):
                        raise HTTPException(status_code=403, detail="no permission for this vehicle")
                    cursor.execute("DELETE FROM vehicle WHERE id=%s", (vehicle_id,))
                    return {"message": "vehicle deleted", "vehicle_id": vehicle_id}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"db error: {exc}") from exc

    if vehicle_id not in _VEHICLES:
        raise HTTPException(status_code=404, detail="vehicle not found")
    if owner_id is not None and str(_VEHICLES[vehicle_id]["owner_id"]) != str(owner_id):
        raise HTTPException(status_code=403, detail="no permission for this vehicle")
    del _VEHICLES[vehicle_id]
    return {"message": "vehicle deleted", "vehicle_id": vehicle_id}
