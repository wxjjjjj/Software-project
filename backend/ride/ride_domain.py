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
    ownerUserId: int = 20001
    plateNo: str
    brand: str = ""
    color: str = ""
    seatCapacity: int = 4


# 编辑车辆接口的请求体（按需更新字段）。
class VehicleUpdateRequest(BaseModel):
    plateNo: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    seatCapacity: Optional[int] = None


# 车辆状态切换接口的请求体。
class VehicleStatusUpdateRequest(BaseModel):
    status: str


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


VEHICLE_STORE = {
    30001: {
        "id": 30001,
        "ownerUserId": 20001,
        "plateNo": "沪A12345",
        "brand": "比亚迪秦",
        "color": "白色",
        "seatCapacity": 5,
        "verified": False,
        "status": "available",
    }
}


# 车辆状态白名单（Mock 与 DB 模式共用）。
ALLOWED_VEHICLE_STATUS = {"available", "disabled"}


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
        raise HTTPException(status_code=400, detail="plateNo cannot be empty")
    return normalized


def _validate_seat_capacity(seat_capacity: int) -> None:
    # 与前端校验保持一致：座位数限定在 2~9。
    if seat_capacity < 2 or seat_capacity > 9:
        raise HTTPException(
            status_code=400,
            detail="seatCapacity must be between 2 and 9",
        )


def _format_vehicle_row(row: dict) -> dict:
    # 把数据库字段映射成前端使用的字段名。
    return {
        "vehicleId": row["id"],
        "ownerUserId": row["owner_user_id"],
        "plateNo": row["plate_no"],
        "brand": row.get("brand") or "",
        "color": row.get("color") or "",
        "seatCapacity": int(row["seat_capacity"]),
        # SQL 里暂未强制要求该字段，先保持兼容前端展示。
        "verified": bool(row.get("verified", 0)),
        "status": row["status"],
    }


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


def list_vehicles(owner_user_id: int = 20001) -> dict:
    # 真实库模式：从 vehicle 表查询车主名下车辆。
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        (
                            "SELECT id, owner_user_id, plate_no, brand, "
                            "color, seat_capacity, status "
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
        if vehicle["ownerUserId"] == owner_user_id
    ]
    items.sort(key=lambda item: item["id"], reverse=True)
    return {"items": items}


def create_vehicle(payload: VehicleCreateRequest) -> dict:
    plate_no = _normalize_plate_no(payload.plateNo)
    _validate_seat_capacity(payload.seatCapacity)

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
                            detail="plateNo already exists",
                        )

                    cursor.execute(
                        (
                            "INSERT INTO vehicle "
                            "(owner_user_id, plate_no, brand, color, "
                            "seat_capacity, status) "
                            "VALUES (%s, %s, %s, %s, %s, 'available')"
                        ),
                        (
                            payload.ownerUserId,
                            plate_no,
                            payload.brand,
                            payload.color,
                            payload.seatCapacity,
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
            "vehicleId": new_vehicle_id,
            "status": "available",
        }

    # Mock 模式：写入内存字典，便于本地快速联调。
    duplicate = any(item["plateNo"] == plate_no for item in VEHICLE_STORE.values())
    if duplicate:
        raise HTTPException(status_code=409, detail="plateNo already exists")

    new_vehicle_id = max(VEHICLE_STORE.keys(), default=30000) + 1
    VEHICLE_STORE[new_vehicle_id] = {
        "id": new_vehicle_id,
        "ownerUserId": payload.ownerUserId,
        "plateNo": plate_no,
        "brand": payload.brand,
        "color": payload.color,
        "seatCapacity": payload.seatCapacity,
        "verified": False,
        "status": "available",
    }
    return {
        "message": "vehicle created",
        "vehicleId": new_vehicle_id,
        "status": "available",
    }


def update_vehicle(vehicle_id: int, payload: VehicleUpdateRequest) -> dict:
    # 至少要传一个可更新字段，避免空更新。
    has_changes = any(
        value is not None
        for value in [
            payload.plateNo,
            payload.brand,
            payload.color,
            payload.seatCapacity,
        ]
    )
    if not has_changes:
        raise HTTPException(status_code=400, detail="no fields to update")

    normalized_plate = None
    if payload.plateNo is not None:
        normalized_plate = _normalize_plate_no(payload.plateNo)
    if payload.seatCapacity is not None:
        _validate_seat_capacity(payload.seatCapacity)

    # 真实库模式：查重后更新，并回读最新数据返回。
    if not RIDE_USE_MOCK:
        try:
            with get_ride_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        (
                            "SELECT id, owner_user_id, plate_no, brand, color, "
                            "seat_capacity, status "
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
                                detail="plateNo already exists",
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
                    if payload.seatCapacity is not None:
                        updates.append("seat_capacity=%s")
                        values.append(payload.seatCapacity)

                    values.append(vehicle_id)
                    cursor.execute(
                        f"UPDATE vehicle SET {', '.join(updates)} WHERE id=%s",
                        tuple(values),
                    )

                    cursor.execute(
                        (
                            "SELECT id, owner_user_id, plate_no, brand, color, "
                            "seat_capacity, status "
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

    if normalized_plate and normalized_plate != vehicle["plateNo"]:
        duplicate = any(
            item["plateNo"] == normalized_plate and item["id"] != vehicle_id
            for item in VEHICLE_STORE.values()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="plateNo already exists")
        vehicle["plateNo"] = normalized_plate

    if payload.brand is not None:
        vehicle["brand"] = payload.brand
    if payload.color is not None:
        vehicle["color"] = payload.color
    if payload.seatCapacity is not None:
        vehicle["seatCapacity"] = payload.seatCapacity

    return {
        "message": "vehicle updated",
        "vehicle": {
            "vehicleId": vehicle["id"],
            "ownerUserId": vehicle["ownerUserId"],
            "plateNo": vehicle["plateNo"],
            "brand": vehicle["brand"],
            "color": vehicle["color"],
            "seatCapacity": vehicle["seatCapacity"],
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
            "vehicleId": vehicle_id,
            "status": next_status,
        }

    # Mock 模式：更新内存状态。
    vehicle = VEHICLE_STORE.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")
    vehicle["status"] = next_status
    return {
        "message": "vehicle status updated",
        "vehicleId": vehicle_id,
        "status": next_status,
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
            "vehicleId": vehicle_id,
        }

    # Mock 模式：删除内存记录。
    vehicle = VEHICLE_STORE.pop(vehicle_id, None)
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")
    return {
        "message": "vehicle deleted",
        "vehicleId": vehicle_id,
    }
