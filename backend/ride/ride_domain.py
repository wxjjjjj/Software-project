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
