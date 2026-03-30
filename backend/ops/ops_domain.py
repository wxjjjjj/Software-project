from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel

from backend.common.config import OPS_USE_MOCK
from backend.ops.ops_db import get_ops_conn


class PayOrderRequest(BaseModel):
    payerUserId: int = 1001
    amount: float = 35.5


class WalletWithdrawRequest(BaseModel):
    ownerUserId: int = 20001
    amount: float = 100.0


class FeedbackCreateRequest(BaseModel):
    userId: int = 1001
    orderId: Optional[int] = None
    content: str = ""


def pay_order(
    order_id: int,
    payload: Optional[PayOrderRequest] = None,
) -> dict:
    req = payload or PayOrderRequest()

    if OPS_USE_MOCK:
        return {
            "message": "payment success",
            "orderId": order_id,
            "status": "PAID",
        }

    try:
        with get_ops_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    (
                        "SELECT id, pay_status FROM payment_order "
                        "WHERE order_id=%s AND payer_user_id=%s "
                        "ORDER BY id DESC LIMIT 1"
                    ),
                    (order_id, req.payerUserId),
                )
                row = cursor.fetchone()

                if row and row["pay_status"] == "PAID":
                    raise HTTPException(
                        status_code=409,
                        detail="order already paid",
                    )

                amount = Decimal(str(req.amount))
                if amount <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail="amount must be positive",
                    )

                if row:
                    cursor.execute(
                        (
                            "UPDATE payment_order SET "
                            "pay_amount=%s, pay_status='PAID', paid_at=%s "
                            "WHERE id=%s"
                        ),
                        (amount, datetime.now(), row["id"]),
                    )
                else:
                    cursor.execute(
                        (
                            "INSERT INTO payment_order "
                            "(order_id, payer_user_id, pay_amount, "
                            "pay_status, paid_at) "
                            "VALUES (%s, %s, %s, 'PAID', %s)"
                        ),
                        (
                            order_id,
                            req.payerUserId,
                            amount,
                            datetime.now(),
                        ),
                    )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ops db error: {exc}",
        ) from exc

    return {
        "message": "payment success",
        "orderId": order_id,
        "status": "PAID",
    }


def wallet_info(owner_user_id: int = 20001) -> dict:
    if OPS_USE_MOCK:
        return {"balance": 512.5, "currency": "CNY"}

    try:
        with get_ops_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    (
                        "SELECT id, balance FROM wallet_account "
                        "WHERE owner_user_id=%s"
                    ),
                    (owner_user_id,),
                )
                row = cursor.fetchone()

                if not row:
                    cursor.execute(
                        (
                            "INSERT INTO wallet_account "
                            "(owner_user_id, balance, frozen_amount) "
                            "VALUES (%s, 0, 0)"
                        ),
                        (owner_user_id,),
                    )
                    return {"balance": 0, "currency": "CNY"}

                return {
                    "balance": float(row["balance"]),
                    "currency": "CNY",
                }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ops db error: {exc}",
        ) from exc


def wallet_withdraw(payload: Optional[WalletWithdrawRequest] = None) -> dict:
    req = payload or WalletWithdrawRequest()

    if OPS_USE_MOCK:
        return {"message": "withdraw request accepted", "requestId": 7788}

    amount = Decimal(str(req.amount))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")

    try:
        with get_ops_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    (
                        "SELECT id, balance, frozen_amount "
                        "FROM wallet_account WHERE owner_user_id=%s"
                    ),
                    (req.ownerUserId,),
                )
                wallet_row = cursor.fetchone()
                if not wallet_row:
                    raise HTTPException(
                        status_code=404,
                        detail="wallet not found",
                    )

                balance = Decimal(str(wallet_row["balance"]))
                frozen = Decimal(str(wallet_row["frozen_amount"]))
                if balance < amount:
                    raise HTTPException(
                        status_code=409,
                        detail="insufficient balance",
                    )

                cursor.execute(
                    (
                        "UPDATE wallet_account SET balance=%s, "
                        "frozen_amount=%s WHERE id=%s"
                    ),
                    (
                        balance - amount,
                        frozen + amount,
                        wallet_row["id"],
                    ),
                )

                cursor.execute(
                    (
                        "INSERT INTO withdraw_request "
                        "(owner_user_id, amount, withdraw_status, "
                        "requested_at) "
                        "VALUES (%s, %s, 'PENDING', %s)"
                    ),
                    (req.ownerUserId, amount, datetime.now()),
                )
                request_id = cursor.lastrowid

                cursor.execute(
                    (
                        "INSERT INTO wallet_txn "
                        "(wallet_id, txn_type, amount, biz_order_id) "
                        "VALUES (%s, 'withdraw', %s, %s)"
                    ),
                    (wallet_row["id"], amount, request_id),
                )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ops db error: {exc}",
        ) from exc

    return {
        "message": "withdraw request accepted",
        "requestId": request_id,
    }


def create_feedback(payload: Optional[FeedbackCreateRequest] = None) -> dict:
    req = payload or FeedbackCreateRequest(
        content="",
    )

    if OPS_USE_MOCK:
        return {"message": "feedback submitted", "feedbackId": 9001}

    if not req.content.strip():
        raise HTTPException(status_code=400, detail="content cannot be empty")

    try:
        with get_ops_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    (
                        "INSERT INTO feedback "
                        "(user_id, related_order_id, content, "
                        "feedback_status) "
                        "VALUES (%s, %s, %s, 'open')"
                    ),
                    (req.userId, req.orderId, req.content.strip()),
                )
                feedback_id = cursor.lastrowid
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ops db error: {exc}",
        ) from exc

    return {"message": "feedback submitted", "feedbackId": feedback_id}


def admin_list_users() -> dict:
    if OPS_USE_MOCK:
        return {
            "items": [
                {"userId": 1, "username": "demo_user", "status": "active"}
            ]
        }

    try:
        with get_ops_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    (
                        "SELECT DISTINCT user_id FROM feedback "
                        "ORDER BY user_id DESC LIMIT 100"
                    )
                )
                rows = cursor.fetchall()
                items = [
                    {
                        "userId": row["user_id"],
                        "username": f"user_{row['user_id']}",
                        "status": "active",
                    }
                    for row in rows
                ]
                return {"items": items}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ops db error: {exc}",
        ) from exc


def admin_list_orders() -> dict:
    if OPS_USE_MOCK:
        return {"items": [{"orderId": 10001, "status": "CREATED"}]}

    try:
        with get_ops_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    (
                        "SELECT order_id, pay_status FROM payment_order "
                        "ORDER BY id DESC LIMIT 100"
                    )
                )
                rows = cursor.fetchall()
                items = [
                    {
                        "orderId": row["order_id"],
                        "status": row["pay_status"],
                    }
                    for row in rows
                ]
                return {"items": items}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ops db error: {exc}",
        ) from exc


def admin_list_feedback() -> dict:
    if OPS_USE_MOCK:
        return {"items": [{"feedbackId": 9001, "status": "open"}]}

    try:
        with get_ops_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    (
                        "SELECT id, feedback_status FROM feedback "
                        "ORDER BY id DESC LIMIT 100"
                    )
                )
                rows = cursor.fetchall()
                items = [
                    {
                        "feedbackId": row["id"],
                        "status": row["feedback_status"],
                    }
                    for row in rows
                ]
                return {"items": items}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ops db error: {exc}",
        ) from exc
