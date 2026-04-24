from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel

from backend.common.config import RIDE_USE_MOCK
from backend.ride.ride_db import get_ride_conn


class OrderPublishRequest(BaseModel):
    role: str = "passenger"
    startLoc: Optional[str] = None
    endLoc: Optional[str] = None
    seatsNeeded: int = 1
    expectedPrice: float = 0


class DriverAcceptRequest(BaseModel):
    ownerId: int = 20001
    vehicleId: int = 30001


# 新增车辆接口的请求体。
class VehicleCreateRequest(BaseModel):
    owner_id: Optional[str] = None
    plate_no: str
    brand: str = ""
    color: str = ""
    seat_capacity: int = 4


# 编辑车辆接口的请求体（按需更新字段）。
class VehicleUpdateRequest(BaseModel):
    plate_no: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    seat_capacity: Optional[int] = None


# 车辆状态切换接口的请求体。
class VehicleStatusUpdateRequest(BaseModel):
    status: str


# 管理员修改车辆认证状态接口的请求体。
class VehicleVerifyUpdateRequest(BaseModel):
    verified: bool


# 车主提交车辆认证资料接口的请求体。
class VehicleVerifySubmitRequest(BaseModel):
    owner_name: str
    id_no: str
    driver_license_no: str
    vehicle_license_no: str
    contact_phone: str = ""
    remark: str = ""


# 管理员审核车辆认证资料接口的请求体。
class VehicleVerifyReviewRequest(BaseModel):
    decision: str  # approved / rejected
    review_note: str = ""


ORDER_STORE = {
    10001: {
        "orderId": 10001,
        "passengerId": 1001,
        "from": "软件园",
        "to": "大学城",
        "status": "CREATED",
        "ownerId": None,
        "vehicleId": None,
        "lockedTime": None,
    }
}


VEHICLE_STORE = {}

VEHICLE_VERIFY_REQUEST_STORE = {}


# 车辆状态白名单（Mock 与 DB 模式共用）。
ALLOWED_VEHICLE_STATUS = {"available", "disabled"}
ALLOWED_VERIFY_REQUEST_STATUS = {"pending", "approved", "rejected"}


def _format_order_row(row: dict) -> dict:
    locked_time = row.get("locked_time")
    if isinstance(locked_time, datetime):
        locked_time = locked_time.isoformat(timespec="seconds")
    return {
        "orderId": row["id"],
        "from": row["from_text"],
        "to": row["to_text"],
        "tag": ["早高峰", "顺路"],
        "status": row["order_status"],
        "ownerId": row.get("owner_user_id"),
        "vehicleId": row.get("vehicle_id"),
        "lockedTime": locked_time,
    }


def _normalize_plate_no(plate_no: str) -> str:
    # 统一车牌格式，便于去重比较。
    normalized = (plate_no or "").strip().upper()
    if not normalized:
        raise HTTPException(status_code=400, detail="plate_no cannot be empty")
    return normalized


def _validate_seat_capacity(seat_capacity: int) -> None:
    # 与前端校验保持一致：座位数限定在 2~9。
    if seat_capacity < 2 or seat_capacity > 9:
        raise HTTPException(
            status_code=400,
            detail="seat_capacity must be between 2 and 9",
        )


def _as_bool(value) -> bool:
    # 统一解析布尔值，避免把字符串 "0" / "false" 误判为 True。
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


def _format_vehicle_row(row: dict) -> dict:
    # 把数据库字段映射成前端使用的字段名。
    return {
        "vehicle_id": row["id"],
        "owner_id": str(row["owner_user_id"]),
        "plate_no": row["plate_no"],
        "brand": row.get("brand") or "",
        "color": row.get("color") or "",
        "seat_capacity": int(row["seat_capacity"]),
        # SQL 里暂未强制要求该字段，先保持兼容前端展示。
        "verified": _as_bool(row.get("verified", 0)),
        "status": row["status"],
    }


def _format_verify_request_row(row: dict) -> dict:
    return {
        "request_id": row["id"],
        "vehicle_id": row["vehicle_id"],
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
        "reviewed_at": row.get("reviewed_at").isoformat(timespec="seconds")
        if isinstance(row.get("reviewed_at"), datetime)
        else row.get("reviewed_at"),
        "created_at": row.get("created_at").isoformat(timespec="seconds")
        if isinstance(row.get("created_at"), datetime)
        else row.get("created_at"),
        "vehicle": {
            "plate_no": row.get("plate_no") or "",
            "brand": row.get("brand") or "",
            "color": row.get("color") or "",
            "seat_capacity": int(row.get("seat_capacity") or 0),
            "verified": _as_bool(row.get("verified", 0)),
        },
    }


def _mask_id_no(id_no: str) -> str:
    text = (id_no or "").strip()
    if len(text) <= 8:
        return text
    return f"{text[:4]}****{text[-4:]}"


def search_orders() -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        (
                            "SELECT id, from_text, to_text, order_status, "
                            "owner_user_id, vehicle_id, locked_time "
                            "FROM ride_order ORDER BY id DESC LIMIT 100"
                        )
                    )
                    rows = cursor.fetchall()
                    return {"items": [_format_order_row(row) for row in rows]}
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"ride db error: {exc}",
            ) from exc

    items = []
    for order in ORDER_STORE.values():
        items.append(
            {
                "orderId": order["orderId"],
                "from": order["from"],
                "to": order["to"],
                "tag": ["早高峰", "顺路"],
                "status": order["status"],
                "ownerId": order["ownerId"],
                "vehicleId": order["vehicleId"],
                "lockedTime": order["lockedTime"],
            }
        )
    return {"items": items}


def publish_order(payload: OrderPublishRequest) -> dict:
    if payload.role.lower() == "owner":
        raise HTTPException(
            status_code=403,
            detail="Owner cannot publish order",
        )

    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        (
                            "INSERT INTO ride_order "
                            "(passenger_user_id, from_text, to_text, "
                            "depart_time, "
                            "seat_count, expected_price, order_status) "
                            "VALUES (%s, %s, %s, %s, %s, %s, 'CREATED')"
                        ),
                        (
                            1002,
                            payload.startLoc or "默认出发地",
                            payload.endLoc or "默认目的地",
                            datetime.now(),
                            payload.seatsNeeded,
                            payload.expectedPrice,
                        ),
                    )
                    new_order_id = cursor.lastrowid
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"ride db error: {exc}",
            ) from exc
    else:
        new_order_id = max(ORDER_STORE.keys(), default=10000) + 1
        ORDER_STORE[new_order_id] = {
            "orderId": new_order_id,
            "passengerId": 1002,
            "from": payload.startLoc or "默认出发地",
            "to": payload.endLoc or "默认目的地",
            "status": "CREATED",
            "ownerId": None,
            "vehicleId": None,
            "lockedTime": None,
        }

    return {
        "message": "order created",
        "orderId": new_order_id,
        "status": "CREATED",
    }


def driver_accept(order_id: int, payload: DriverAcceptRequest) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        (
                            "SELECT id, order_status FROM ride_order "
                            "WHERE id=%s"
                        ),
                        (order_id,),
                    )
                    row = cursor.fetchone()
                    if not row:
                        raise HTTPException(
                            status_code=404,
                            detail="Order not found",
                        )
                    if row["order_status"] != "CREATED":
                        raise HTTPException(
                            status_code=409,
                            detail="Order cannot be accepted again",
                        )

                    cursor.execute(
                        (
                            "UPDATE ride_order SET "
                            "owner_user_id=%s, vehicle_id=%s, locked_time=%s, "
                            "order_status='LOCKED' WHERE id=%s"
                        ),
                        (
                            payload.ownerId,
                            payload.vehicleId,
                            datetime.now(),
                            order_id,
                        ),
                    )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"ride db error: {exc}",
            ) from exc

        return {
            "message": "driver accepted and order locked",
            "orderId": order_id,
            "status": "LOCKED",
            "ownerId": payload.ownerId,
            "vehicleId": payload.vehicleId,
            "lockedTime": datetime.now().isoformat(timespec="seconds"),
        }

    order = ORDER_STORE.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] != "CREATED":
        raise HTTPException(
            status_code=409,
            detail="Order cannot be accepted again",
        )

    order["ownerId"] = payload.ownerId
    order["vehicleId"] = payload.vehicleId
    order["lockedTime"] = datetime.now().isoformat(timespec="seconds")
    order["status"] = "LOCKED"

    return {
        "message": "driver accepted and order locked",
        "orderId": order_id,
        "status": order["status"],
        "ownerId": order["ownerId"],
        "vehicleId": order["vehicleId"],
        "lockedTime": order["lockedTime"],
    }


def passenger_confirm(order_id: int) -> dict:
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        (
                            "SELECT id, order_status FROM ride_order "
                            "WHERE id=%s"
                        ),
                        (order_id,),
                    )
                    row = cursor.fetchone()
                    if not row:
                        raise HTTPException(
                            status_code=404,
                            detail="Order not found",
                        )
                    if row["order_status"] not in {
                        "LOCKED",
                        "PASSENGER_CONFIRMED",
                    }:
                        raise HTTPException(
                            status_code=409,
                            detail="Order is not ready for passenger confirm",
                        )
                    cursor.execute(
                        (
                            "UPDATE ride_order SET "
                            "order_status='PASSENGER_CONFIRMED' "
                            "WHERE id=%s"
                        ),
                        (order_id,),
                    )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"ride db error: {exc}",
            ) from exc

        return {
            "message": "passenger confirmed",
            "orderId": order_id,
            "status": "PASSENGER_CONFIRMED",
        }

    order = ORDER_STORE.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "message": "passenger confirmed",
        "orderId": order_id,
        "status": "PASSENGER_CONFIRMED",
    }


def list_vehicles(owner_user_id: str = "dev-user-1") -> dict:
    # 真实库模式：从 vehicle 表查询车主名下车辆。
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        (
                            "SELECT id, owner_user_id, plate_no, brand, "
                            "color, seat_capacity, verified, status "
                            "FROM vehicle WHERE owner_user_id=%s "
                            "ORDER BY id DESC"
                        ),
                        (owner_user_id,),
                    )
                    rows = cursor.fetchall()
                    items = [_format_vehicle_row(row) for row in rows]
                    return {"items": items}
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"ride db error: {exc}",
            ) from exc

    # Mock 模式：返回内存中的车辆数据。
    items = [
        vehicle
        for vehicle in VEHICLE_STORE.values()
        if vehicle["owner_id"] == owner_user_id
    ]
    items.sort(key=lambda item: item["vehicle_id"], reverse=True)
    return {"items": items}


def create_vehicle(
    payload: VehicleCreateRequest,
    owner_user_id: Optional[str] = None,
) -> dict:
    plate_no = _normalize_plate_no(payload.plate_no)
    _validate_seat_capacity(payload.seat_capacity)
    resolved_owner_id = owner_user_id or payload.owner_id
    if not resolved_owner_id:
        raise HTTPException(status_code=400, detail="owner_id is required")

    # 真实库模式：写入数据库并返回新主键。
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM vehicle WHERE plate_no=%s",
                        (plate_no,),
                    )
                    exists = cursor.fetchone()
                    if exists:
                        raise HTTPException(
                            status_code=409,
                            detail="plate_no already exists",
                        )

                    cursor.execute(
                        (
                            "INSERT INTO vehicle "
                            "(owner_user_id, plate_no, brand, color, "
                            "seat_capacity, status) "
                            "VALUES (%s, %s, %s, %s, %s, 'available')"
                        ),
                        (
                            resolved_owner_id,
                            plate_no,
                            payload.brand,
                            payload.color,
                            payload.seat_capacity,
                        ),
                    )
                    new_vehicle_id = cursor.lastrowid
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"ride db error: {exc}",
            ) from exc

        return {
            "message": "vehicle created",
            "vehicle_id": new_vehicle_id,
            "status": "available",
        }

    # Mock 模式：写入内存字典，便于本地快速联调。
    duplicate = any(item["plate_no"] == plate_no for item in VEHICLE_STORE.values())
    if duplicate:
        raise HTTPException(status_code=409, detail="plate_no already exists")

    new_vehicle_id = max(VEHICLE_STORE.keys(), default=30000) + 1
    VEHICLE_STORE[new_vehicle_id] = {
        "vehicle_id": new_vehicle_id,
        "owner_id": resolved_owner_id,
        "plate_no": plate_no,
        "brand": payload.brand,
        "color": payload.color,
        "seat_capacity": payload.seat_capacity,
        "verified": False,
        "status": "available",
    }
    return {
        "message": "vehicle created",
        "vehicle_id": new_vehicle_id,
        "status": "available",
    }


def update_vehicle(vehicle_id: int, payload: VehicleUpdateRequest) -> dict:
    # 至少要传一个可更新字段，避免空更新。
    has_changes = any(
        value is not None
        for value in [
            payload.plate_no,
            payload.brand,
            payload.color,
            payload.seat_capacity,
        ]
    )
    if not has_changes:
        raise HTTPException(status_code=400, detail="no fields to update")

    normalized_plate = None
    if payload.plate_no is not None:
        normalized_plate = _normalize_plate_no(payload.plate_no)
    if payload.seat_capacity is not None:
        _validate_seat_capacity(payload.seat_capacity)

    # 真实库模式：查重后更新，并回读最新数据返回。
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        (
                            "SELECT id, owner_user_id, plate_no, brand, color, "
                            "seat_capacity, verified, status "
                            "FROM vehicle WHERE id=%s"
                        ),
                        (vehicle_id,),
                    )
                    existing = cursor.fetchone()
                    if not existing:
                        raise HTTPException(
                            status_code=404,
                            detail="vehicle not found",
                        )

                    if normalized_plate and normalized_plate != existing["plate_no"]:
                        cursor.execute(
                            "SELECT id FROM vehicle WHERE plate_no=%s",
                            (normalized_plate,),
                        )
                        plate_owner = cursor.fetchone()
                        if plate_owner:
                            raise HTTPException(
                                status_code=409,
                                detail="plate_no already exists",
                            )

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
                    cursor.execute(
                        f"UPDATE vehicle SET {', '.join(updates)} WHERE id=%s",
                        tuple(values),
                    )

                    cursor.execute(
                        (
                            "SELECT id, owner_user_id, plate_no, brand, color, "
                            "seat_capacity, verified, status "
                            "FROM vehicle WHERE id=%s"
                        ),
                        (vehicle_id,),
                    )
                    updated = cursor.fetchone()
                    return {
                        "message": "vehicle updated",
                        "vehicle": _format_vehicle_row(updated),
                    }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"ride db error: {exc}",
            ) from exc

    # Mock 模式：在内存中执行同等更新逻辑。
    vehicle = VEHICLE_STORE.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")

    if normalized_plate and normalized_plate != vehicle["plate_no"]:
        duplicate = any(
            item["plate_no"] == normalized_plate and item["vehicle_id"] != vehicle_id
            for item in VEHICLE_STORE.values()
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

    return {
        "message": "vehicle updated",
        "vehicle": {
            "vehicle_id": vehicle["vehicle_id"],
            "owner_id": vehicle["owner_id"],
            "plate_no": vehicle["plate_no"],
            "brand": vehicle["brand"],
            "color": vehicle["color"],
            "seat_capacity": vehicle["seat_capacity"],
            "verified": vehicle["verified"],
            "status": vehicle["status"],
        },
    }


def update_vehicle_status(
    vehicle_id: int,
    payload: VehicleStatusUpdateRequest,
) -> dict:
    # 统一状态值格式并做白名单校验。
    next_status = (payload.status or "").strip().lower()
    if next_status not in ALLOWED_VEHICLE_STATUS:
        raise HTTPException(
            status_code=400,
            detail="status must be one of: available, disabled",
        )

    # 真实库模式：更新数据库状态字段。
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM vehicle WHERE id=%s",
                        (vehicle_id,),
                    )
                    exists = cursor.fetchone()
                    if not exists:
                        raise HTTPException(
                            status_code=404,
                            detail="vehicle not found",
                        )

                    cursor.execute(
                        "UPDATE vehicle SET status=%s WHERE id=%s",
                        (next_status, vehicle_id),
                    )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"ride db error: {exc}",
            ) from exc

        return {
            "message": "vehicle status updated",
            "vehicle_id": vehicle_id,
            "status": next_status,
        }

    # Mock 模式：更新内存状态。
    vehicle = VEHICLE_STORE.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")
    vehicle["status"] = next_status
    return {
        "message": "vehicle status updated",
        "vehicle_id": vehicle_id,
        "status": next_status,
    }


def update_vehicle_verified(
    vehicle_id: int,
    payload: VehicleVerifyUpdateRequest,
) -> dict:
    # 管理员变更认证状态，统一布尔值到 0/1 落库。
    verified_value = 1 if payload.verified else 0

    # 真实库模式：更新 verified 字段。
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM vehicle WHERE id=%s",
                        (vehicle_id,),
                    )
                    exists = cursor.fetchone()
                    if not exists:
                        raise HTTPException(
                            status_code=404,
                            detail="vehicle not found",
                        )

                    cursor.execute(
                        "UPDATE vehicle SET verified=%s WHERE id=%s",
                        (verified_value, vehicle_id),
                    )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"ride db error: {exc}",
            ) from exc

        return {
            "message": "vehicle verification updated",
            "vehicle_id": vehicle_id,
            "verified": payload.verified,
        }

    # Mock 模式：更新内存字段。
    vehicle = VEHICLE_STORE.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")
    vehicle["verified"] = payload.verified
    return {
        "message": "vehicle verification updated",
        "vehicle_id": vehicle_id,
        "verified": payload.verified,
    }


def submit_vehicle_verify_request(
    vehicle_id: int,
    payload: VehicleVerifySubmitRequest,
    owner_user_id: str,
) -> dict:
    # 真实库模式：校验车辆归属并写入待审核资料。
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
                    if str(vehicle["owner_user_id"]) != str(owner_user_id):
                        raise HTTPException(status_code=403, detail="no permission for this vehicle")
                    if _as_bool(vehicle.get("verified", 0)):
                        raise HTTPException(status_code=409, detail="vehicle already verified")

                    cursor.execute(
                        (
                            "SELECT id FROM vehicle_verify_request "
                            "WHERE vehicle_id=%s AND status='pending' LIMIT 1"
                        ),
                        (vehicle_id,),
                    )
                    pending = cursor.fetchone()
                    if pending:
                        raise HTTPException(status_code=409, detail="verification request already pending")

                    cursor.execute(
                        (
                            "INSERT INTO vehicle_verify_request "
                            "(vehicle_id, owner_user_id, owner_name, id_no, "
                            "driver_license_no, vehicle_license_no, contact_phone, remark, status) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')"
                        ),
                        (
                            vehicle_id,
                            owner_user_id,
                            payload.owner_name,
                            payload.id_no,
                            payload.driver_license_no,
                            payload.vehicle_license_no,
                            payload.contact_phone,
                            payload.remark,
                        ),
                    )
                    request_id = cursor.lastrowid
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"ride db error: {exc}") from exc

        return {
            "message": "vehicle verification request submitted",
            "request_id": request_id,
            "vehicle_id": vehicle_id,
            "status": "pending",
        }

    # Mock 模式：在内存中记录待审核资料。
    vehicle = VEHICLE_STORE.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")
    if str(vehicle["owner_id"]) != str(owner_user_id):
        raise HTTPException(status_code=403, detail="no permission for this vehicle")
    if _as_bool(vehicle.get("verified", False)):
        raise HTTPException(status_code=409, detail="vehicle already verified")

    exists_pending = any(
        item["vehicle_id"] == vehicle_id and item["status"] == "pending"
        for item in VEHICLE_VERIFY_REQUEST_STORE.values()
    )
    if exists_pending:
        raise HTTPException(status_code=409, detail="verification request already pending")

    request_id = max(VEHICLE_VERIFY_REQUEST_STORE.keys(), default=90000) + 1
    VEHICLE_VERIFY_REQUEST_STORE[request_id] = {
        "request_id": request_id,
        "vehicle_id": vehicle_id,
        "owner_user_id": owner_user_id,
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
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "vehicle": {
            "plate_no": vehicle["plate_no"],
            "brand": vehicle["brand"],
            "color": vehicle["color"],
            "seat_capacity": vehicle["seat_capacity"],
            "verified": _as_bool(vehicle.get("verified", False)),
        },
    }
    return {
        "message": "vehicle verification request submitted",
        "request_id": request_id,
        "vehicle_id": vehicle_id,
        "status": "pending",
    }


def list_vehicle_verify_requests(status: Optional[str] = "pending") -> dict:
    normalized_status = None
    if status:
        normalized_status = status.strip().lower()
        if normalized_status and normalized_status not in ALLOWED_VERIFY_REQUEST_STATUS:
            raise HTTPException(
                status_code=400,
                detail="status must be one of: pending, approved, rejected",
            )

    # 真实库模式：读取认证申请列表。
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    sql = (
                        "SELECT r.id, r.vehicle_id, r.owner_user_id, r.owner_name, r.id_no, "
                        "r.driver_license_no, r.vehicle_license_no, r.contact_phone, r.remark, "
                        "r.status, r.review_note, r.reviewed_by, r.reviewed_at, r.created_at, "
                        "v.plate_no, v.brand, v.color, v.seat_capacity, v.verified "
                        "FROM vehicle_verify_request r "
                        "JOIN vehicle v ON v.id=r.vehicle_id "
                    )
                    args = ()
                    if normalized_status:
                        sql += "WHERE r.status=%s "
                        args = (normalized_status,)
                    sql += "ORDER BY r.created_at DESC"
                    cursor.execute(sql, args)
                    rows = cursor.fetchall()

                    items = []
                    for row in rows:
                        item = _format_verify_request_row(row)
                        item["id_no_masked"] = _mask_id_no(item["id_no"])
                        items.append(item)
                    return {"items": items}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"ride db error: {exc}") from exc

    # Mock 模式：过滤并返回内存申请。
    items = []
    for req in VEHICLE_VERIFY_REQUEST_STORE.values():
        if normalized_status and req["status"] != normalized_status:
            continue
        item = dict(req)
        item["id_no_masked"] = _mask_id_no(item.get("id_no", ""))
        items.append(item)
    items.sort(key=lambda x: x.get("request_id", 0), reverse=True)
    return {"items": items}


def review_vehicle_verify_request(
    request_id: int,
    payload: VehicleVerifyReviewRequest,
    reviewer_user_id: str,
) -> dict:
    decision = (payload.decision or "").strip().lower()
    if decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="decision must be approved or rejected")

    # 真实库模式：更新申请状态并在通过时更新车辆认证。
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, vehicle_id, status FROM vehicle_verify_request WHERE id=%s",
                        (request_id,),
                    )
                    req = cursor.fetchone()
                    if not req:
                        raise HTTPException(status_code=404, detail="verification request not found")
                    if req["status"] != "pending":
                        raise HTTPException(status_code=409, detail="verification request already reviewed")

                    cursor.execute(
                        (
                            "UPDATE vehicle_verify_request SET "
                            "status=%s, review_note=%s, reviewed_by=%s, reviewed_at=%s "
                            "WHERE id=%s"
                        ),
                        (decision, payload.review_note, reviewer_user_id, datetime.now(), request_id),
                    )

                    if decision == "approved":
                        cursor.execute(
                            "UPDATE vehicle SET verified=1 WHERE id=%s",
                            (req["vehicle_id"],),
                        )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"ride db error: {exc}") from exc

        return {
            "message": "vehicle verification request reviewed",
            "request_id": request_id,
            "decision": decision,
        }

    # Mock 模式：更新申请与车辆字段。
    req = VEHICLE_VERIFY_REQUEST_STORE.get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="verification request not found")
    if req["status"] != "pending":
        raise HTTPException(status_code=409, detail="verification request already reviewed")

    req["status"] = decision
    req["review_note"] = payload.review_note
    req["reviewed_by"] = reviewer_user_id
    req["reviewed_at"] = datetime.now().isoformat(timespec="seconds")

    if decision == "approved":
        vehicle = VEHICLE_STORE.get(req["vehicle_id"])
        if vehicle:
            vehicle["verified"] = True

    return {
        "message": "vehicle verification request reviewed",
        "request_id": request_id,
        "decision": decision,
    }


def delete_vehicle(vehicle_id: int) -> dict:
    # 真实库模式：删除数据库记录。
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM vehicle WHERE id=%s",
                        (vehicle_id,),
                    )
                    exists = cursor.fetchone()
                    if not exists:
                        raise HTTPException(
                            status_code=404,
                            detail="vehicle not found",
                        )

                    cursor.execute(
                        "DELETE FROM vehicle WHERE id=%s",
                        (vehicle_id,),
                    )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"ride db error: {exc}",
            ) from exc

        return {
            "message": "vehicle deleted",
            "vehicle_id": vehicle_id,
        }

    # Mock 模式：删除内存记录。
    vehicle = VEHICLE_STORE.pop(vehicle_id, None)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")
    return {
        "message": "vehicle deleted",
        "vehicle_id": vehicle_id,
    }
