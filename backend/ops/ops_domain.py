from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel

from backend.common.config import OPS_USE_MOCK
from backend.ops.ops_db import get_ops_conn


class PayOrderRequest(BaseModel):
    payerUserId: int
    payeeUserId: int
    amount: float
    idempotencyKey: str = ""


class WalletWithdrawRequest(BaseModel):
    userId: int
    amount: float


class SendMessageRequest(BaseModel):
    orderId: str
    senderId: int
    receiverId: int
    content: str


class CreateComplaintRequest(BaseModel):
    orderId: Optional[str] = None
    plaintiffId: int
    defendantId: Optional[int] = None
    reasonType: int = 0
    detail: str
    evidenceUrls: str = ""


class HandleComplaintRequest(BaseModel):
    adminId: int
    status: int
    adminReply: str = ""


def _get_wallet(cursor, uid: int) -> dict:
    cursor.execute(
        "SELECT wallet_id, user_id, balance, frozen_amount, status "
        "FROM ops_wallet WHERE user_id=%s", (uid,))
    row = cursor.fetchone()
    if row:
        return row
    cursor.execute(
        "INSERT INTO ops_wallet (user_id, balance, frozen_amount) VALUES (%s, 0, 0)",
        (uid,))
    return {"wallet_id": cursor.lastrowid, "user_id": uid,
            "balance": Decimal("0"), "frozen_amount": Decimal("0"), "status": 1}


def _write_log(cur, uid, change, b_before, b_after, biz, ref=None,
               idem_key=None, cp_id=None, remark=None):
    cur.execute(
        "INSERT INTO ops_wallet_log (user_id, amount_change, balance_before, "
        "balance_after, biz_type, biz_ref_id, idempotency_key, counterparty_id, remark) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (uid, change, b_before, b_after, biz, ref, idem_key, cp_id, remark))
    return cur.lastrowid


def _chk_idem(cur, key: str) -> Optional[dict]:
    if not key:
        return None
    cur.execute("SELECT log_id, status FROM ops_wallet_log WHERE idempotency_key=%s", (key,))
    return cur.fetchone()


def pay_order(order_id: str, payload: PayOrderRequest) -> dict:
    if OPS_USE_MOCK:
        return {"message": "payment success", "orderId": order_id, "status": "PAID"}
    amt = Decimal(str(payload.amount))
    if amt <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            exist = _chk_idem(cur, payload.idempotencyKey)
            if exist:
                return {"message": "already processed", "orderId": order_id,
                        "status": "PAID", "logId": exist["log_id"]}
            pw = _get_wallet(cur, payload.payerUserId)
            rw = _get_wallet(cur, payload.payeeUserId)
            pb = Decimal(str(pw["balance"]))
            if pb < amt:
                raise HTTPException(status_code=409, detail="insufficient balance")
            n_pb = pb - amt
            cur.execute("UPDATE ops_wallet SET balance=%s WHERE wallet_id=%s", (n_pb, pw["wallet_id"]))
            _write_log(cur, payload.payerUserId, -amt, pb, n_pb, 1, order_id,
                       payload.idempotencyKey or None, payload.payeeUserId, f"pay {order_id}")
            rb = Decimal(str(rw["balance"]))
            n_rb = rb + amt
            cur.execute("UPDATE ops_wallet SET balance=%s WHERE wallet_id=%s", (n_rb, rw["wallet_id"]))
            _write_log(cur, payload.payeeUserId, amt, rb, n_rb, 1, order_id,
                       None, payload.payerUserId, f"receive {order_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e
    return {"message": "payment success", "orderId": order_id, "status": "PAID"}


def wallet_info(user_id: int) -> dict:
    if OPS_USE_MOCK:
        return {"balance": 512.5, "frozenAmount": 0, "currency": "CNY"}
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            w = _get_wallet(cur, user_id)
            return {"balance": float(w["balance"]),
                    "frozenAmount": float(w["frozen_amount"]), "currency": "CNY"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e


def wallet_withdraw(payload: WalletWithdrawRequest) -> dict:
    if OPS_USE_MOCK:
        return {"message": "withdraw request accepted", "requestId": 7788}
    amt = Decimal(str(payload.amount))
    if amt <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            w = _get_wallet(cur, payload.userId)
            bal, frz = Decimal(str(w["balance"])), Decimal(str(w["frozen_amount"]))
            if bal < amt:
                raise HTTPException(status_code=409, detail="insufficient balance")
            n_bal, n_frz = bal - amt, frz + amt
            cur.execute("UPDATE ops_wallet SET balance=%s, frozen_amount=%s WHERE wallet_id=%s",
                        (n_bal, n_frz, w["wallet_id"]))
            log_id = _write_log(cur, payload.userId, -amt, bal, n_bal, 2, remark="withdraw")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e
    return {"message": "withdraw request accepted", "requestId": log_id}


def wallet_logs(user_id: int, page: int = 1, size: int = 20) -> dict:
    if OPS_USE_MOCK:
        return {"items": [{"logId": 1, "amountChange": -35.5, "balanceAfter": 477.0,
                           "bizType": 1, "remark": "pay order 10001",
                           "createdAt": "2025-01-01T12:00:00"}],
                "total": 1, "page": page, "size": size}
    off = (page - 1) * size
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM ops_wallet_log WHERE user_id=%s", (user_id,))
            total = cur.fetchone()["c"]
            cur.execute(
                "SELECT log_id, amount_change, balance_before, balance_after, "
                "biz_type, biz_ref_id, counterparty_id, remark, created_at "
                "FROM ops_wallet_log WHERE user_id=%s ORDER BY log_id DESC LIMIT %s OFFSET %s",
                (user_id, size, off))
            items = [{"logId": r["log_id"], "amountChange": float(r["amount_change"]),
                      "balanceBefore": float(r["balance_before"]),
                      "balanceAfter": float(r["balance_after"]),
                      "bizType": r["biz_type"], "bizRefId": r["biz_ref_id"],
                      "counterpartyId": r["counterparty_id"], "remark": r["remark"],
                      "createdAt": r["created_at"].isoformat() if r["created_at"] else None}
                     for r in cur.fetchall()]
            return {"items": items, "total": total, "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e


def send_message(payload: SendMessageRequest) -> dict:
    if OPS_USE_MOCK:
        return {"message": "sent", "msgId": 5001}
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="content cannot be empty")
    if payload.senderId == payload.receiverId:
        raise HTTPException(status_code=400, detail="cannot send message to yourself")
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ops_chat_message (order_id, sender_id, receiver_id, content) "
                "VALUES (%s, %s, %s, %s)",
                (payload.orderId, payload.senderId, payload.receiverId, payload.content.strip()))
            mid = cur.lastrowid
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e
    return {"message": "sent", "msgId": mid}


def get_messages(order_id: str, user_id: int, target_user_id: Optional[int] = None,
                 page: int = 1, size: int = 50) -> dict:
    if OPS_USE_MOCK:
        return {"items": [{"msgId": 5001, "senderId": 1001, "receiverId": 20001,
                           "content": "Hello", "isRead": 1, "sendTime": "2025-01-01T12:00:00"}],
                "total": 1, "page": page, "size": size}
    off = (page - 1) * size
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            if target_user_id is None:
                cur.execute(
                    "SELECT COUNT(*) AS c FROM ops_chat_message "
                    "WHERE order_id=%s AND (sender_id=%s OR receiver_id=%s)",
                    (order_id, user_id, user_id))
            else:
                cur.execute(
                    "SELECT COUNT(*) AS c FROM ops_chat_message "
                    "WHERE order_id=%s AND ((sender_id=%s AND receiver_id=%s) "
                    "OR (sender_id=%s AND receiver_id=%s))",
                    (order_id, user_id, target_user_id, target_user_id, user_id))
            total = cur.fetchone()["c"]
            if target_user_id is None:
                cur.execute(
                    "SELECT msg_id, sender_id, receiver_id, content, is_read, send_time "
                    "FROM ops_chat_message WHERE order_id=%s AND (sender_id=%s OR receiver_id=%s) "
                    "ORDER BY msg_id DESC LIMIT %s OFFSET %s",
                    (order_id, user_id, user_id, size, off))
            else:
                cur.execute(
                    "SELECT msg_id, sender_id, receiver_id, content, is_read, send_time "
                    "FROM ops_chat_message WHERE order_id=%s "
                    "AND ((sender_id=%s AND receiver_id=%s) "
                    "OR (sender_id=%s AND receiver_id=%s)) "
                    "ORDER BY msg_id DESC LIMIT %s OFFSET %s",
                    (order_id, user_id, target_user_id, target_user_id, user_id, size, off))
            items = [{"msgId": r["msg_id"], "senderId": r["sender_id"],
                      "receiverId": r["receiver_id"], "content": r["content"],
                      "isRead": r["is_read"],
                      "sendTime": r["send_time"].isoformat() if r["send_time"] else None}
                     for r in reversed(cur.fetchall())]
            return {"items": items, "total": total, "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e


def mark_messages_read(order_id: str, user_id: int, target_user_id: Optional[int] = None) -> dict:
    if OPS_USE_MOCK:
        return {"message": "marked as read", "count": 1}
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            if target_user_id is None:
                cur.execute(
                    "UPDATE ops_chat_message SET is_read=1 "
                    "WHERE order_id=%s AND receiver_id=%s AND is_read=0",
                    (order_id, user_id))
            else:
                cur.execute(
                    "UPDATE ops_chat_message SET is_read=1 "
                    "WHERE order_id=%s AND sender_id=%s AND receiver_id=%s AND is_read=0",
                    (order_id, target_user_id, user_id))
            cnt = cur.rowcount
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e
    return {"message": "marked as read", "count": cnt}


def create_complaint(payload: CreateComplaintRequest) -> dict:
    if OPS_USE_MOCK:
        return {"message": "complaint submitted", "ticketId": 7001}
    if not payload.detail.strip():
        raise HTTPException(status_code=400, detail="detail cannot be empty")
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ops_complaint (order_id, plaintiff_id, defendant_id, "
                "reason_type, detail, evidence_urls, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, 0)",
                (payload.orderId, payload.plaintiffId, payload.defendantId,
                 payload.reasonType, payload.detail.strip(), payload.evidenceUrls or None))
            tid = cur.lastrowid
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e
    return {"message": "complaint submitted", "ticketId": tid}


def list_complaints(user_id: int, page: int = 1, size: int = 20) -> dict:
    if OPS_USE_MOCK:
        return {"items": [{"ticketId": 7001, "reasonType": 1, "status": 0,
                           "detail": "Driver was late", "createdAt": "2025-01-01T12:00:00"}],
                "total": 1, "page": page, "size": size}
    off = (page - 1) * size
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM ops_complaint WHERE plaintiff_id=%s", (user_id,))
            total = cur.fetchone()["c"]
            cur.execute(
                "SELECT ticket_id, order_id, plaintiff_id, defendant_id, reason_type, detail, "
                "evidence_urls, status, admin_reply, created_at "
                "FROM ops_complaint WHERE plaintiff_id=%s ORDER BY ticket_id DESC LIMIT %s OFFSET %s",
                (user_id, size, off))
            items = [_c2d(r) for r in cur.fetchall()]
            return {"items": items, "total": total, "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e


def admin_list_complaints(status: Optional[int] = None, page: int = 1, size: int = 20) -> dict:
    if OPS_USE_MOCK:
        return {"items": [{"ticketId": 7001, "plaintiffId": 1001, "reasonType": 1,
                           "status": 0, "detail": "Driver was late",
                           "createdAt": "2025-01-01T12:00:00"}],
                "total": 1, "page": page, "size": size}
    off = (page - 1) * size
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            if status is not None:
                cur.execute("SELECT COUNT(*) AS c FROM ops_complaint WHERE status=%s", (status,))
                total = cur.fetchone()["c"]
                cur.execute(
                    "SELECT ticket_id, order_id, plaintiff_id, defendant_id, reason_type, "
                    "detail, evidence_urls, status, admin_id, admin_reply, created_at "
                    "FROM ops_complaint WHERE status=%s ORDER BY ticket_id DESC LIMIT %s OFFSET %s",
                    (status, size, off))
            else:
                cur.execute("SELECT COUNT(*) AS c FROM ops_complaint")
                total = cur.fetchone()["c"]
                cur.execute(
                    "SELECT ticket_id, order_id, plaintiff_id, defendant_id, reason_type, "
                    "detail, evidence_urls, status, admin_id, admin_reply, created_at "
                    "FROM ops_complaint ORDER BY ticket_id DESC LIMIT %s OFFSET %s",
                    (size, off))
            items = [_c2d(r) for r in cur.fetchall()]
            return {"items": items, "total": total, "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e


def admin_handle_complaint(ticket_id: int, payload: HandleComplaintRequest) -> dict:
    if OPS_USE_MOCK:
        return {"message": "complaint handled", "ticketId": ticket_id}
    if payload.status not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="invalid target status")
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT ticket_id, status FROM ops_complaint WHERE ticket_id=%s", (ticket_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="complaint not found")
            if row["status"] == 2:
                raise HTTPException(status_code=409, detail="complaint already resolved")
            cur.execute("UPDATE ops_complaint SET status=%s, admin_id=%s, admin_reply=%s WHERE ticket_id=%s",
                        (payload.status, payload.adminId, payload.adminReply or None, ticket_id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e
    return {"message": "complaint handled", "ticketId": ticket_id}


def admin_statistics() -> dict:
    if OPS_USE_MOCK:
        return {"totalWalletCount": 10, "totalPaymentAmount": 50000.0,
                "pendingComplaintCount": 3, "totalMessageCount": 200}
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM ops_wallet")
            wc = cur.fetchone()["c"]
            cur.execute("SELECT COALESCE(SUM(amount_change), 0) AS t FROM ops_wallet_log WHERE biz_type=1")
            tp = float(cur.fetchone()["t"])
            cur.execute("SELECT COUNT(*) AS c FROM ops_complaint WHERE status=0")
            pc = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM ops_chat_message")
            mc = cur.fetchone()["c"]
            return {"totalWalletCount": wc, "totalPaymentAmount": tp,
                    "pendingComplaintCount": pc, "totalMessageCount": mc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e


def admin_list_withdrawals(page: int = 1, size: int = 20) -> dict:
    if OPS_USE_MOCK:
        return {"items": [{"userId": 1, "balance": 500, "frozenAmount": 20, "walletId": 1}],
                "total": 1, "page": page, "size": size}
    off = (page - 1) * size
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM ops_wallet WHERE frozen_amount>0")
            total = cur.fetchone()["c"]
            cur.execute(
                "SELECT wallet_id, user_id, balance, frozen_amount "
                "FROM ops_wallet WHERE frozen_amount>0 ORDER BY wallet_id LIMIT %s OFFSET %s",
                (size, off))
            items = [{"walletId": r["wallet_id"], "userId": r["user_id"],
                      "balance": float(r["balance"]), "frozenAmount": float(r["frozen_amount"])}
                     for r in cur.fetchall()]
            return {"items": items, "total": total, "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e


def admin_approve_withdrawal(user_id: int) -> dict:
    if OPS_USE_MOCK:
        return {"message": "withdrawal approved", "userId": user_id}
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            w = _get_wallet(cur, user_id)
            frz = Decimal(str(w["frozen_amount"]))
            if frz <= 0:
                raise HTTPException(status_code=409, detail="no pending withdrawal")
            cur.execute("UPDATE ops_wallet SET frozen_amount=0 WHERE wallet_id=%s", (w["wallet_id"],))
            bal = float(w["balance"])
            _write_log(cur, user_id, -float(frz), bal, bal, 2, remark="withdraw_approved")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e
    return {"message": "withdrawal approved", "userId": user_id}


def admin_reject_withdrawal(user_id: int) -> dict:
    if OPS_USE_MOCK:
        return {"message": "withdrawal rejected", "userId": user_id}
    try:
        with get_ops_conn() as conn, conn.cursor() as cur:
            w = _get_wallet(cur, user_id)
            frz = Decimal(str(w["frozen_amount"]))
            if frz <= 0:
                raise HTTPException(status_code=409, detail="no pending withdrawal")
            n_bal = Decimal(str(w["balance"])) + frz
            cur.execute("UPDATE ops_wallet SET balance=%s, frozen_amount=0 WHERE wallet_id=%s",
                        (n_bal, w["wallet_id"]))
            _write_log(cur, user_id, float(frz), float(w["balance"]), float(n_bal), 3,
                       remark="withdraw_rejected")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ops db error: {e}") from e
    return {"message": "withdrawal rejected", "userId": user_id}


def _c2d(r: dict) -> dict:
    return {"ticketId": r["ticket_id"], "orderId": r["order_id"],
            "plaintiffId": r["plaintiff_id"], "defendantId": r["defendant_id"],
            "reasonType": r["reason_type"], "detail": r["detail"],
            "evidenceUrls": r["evidence_urls"], "status": r["status"],
            "adminId": r.get("admin_id"), "adminReply": r.get("admin_reply"),
            "createdAt": r["created_at"].isoformat() if r.get("created_at") else None}
