from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.ops.ops_domain import (
    PayOrderRequest, WalletWithdrawRequest, SendMessageRequest,
    CreateComplaintRequest, HandleComplaintRequest,
    pay_order as domain_pay_order,
    wallet_info as domain_wallet_info,
    wallet_withdraw as domain_wallet_withdraw,
    wallet_logs as domain_wallet_logs,
    send_message as domain_send_message,
    get_messages as domain_get_messages,
    mark_messages_read as domain_mark_messages_read,
    create_complaint as domain_create_complaint,
    list_complaints as domain_list_complaints,
    admin_list_complaints as domain_admin_list_complaints,
    admin_handle_complaint as domain_admin_handle_complaint,
    admin_statistics as domain_admin_statistics,
    admin_list_withdrawals as domain_admin_list_withdrawals,
    admin_approve_withdrawal as domain_admin_approve_withdrawal,
    admin_reject_withdrawal as domain_admin_reject_withdrawal,
)

app = FastAPI(title="Ops Service", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "ops"}


@app.post("/api/payments/orders/{order_id}/pay")
def pay_order(order_id: str, payload: PayOrderRequest):
    return domain_pay_order(order_id, payload)


@app.get("/api/wallet/info")
def wallet_info(user_id: int = Query(1001)):
    return domain_wallet_info(user_id)


@app.post("/api/wallet/withdraw")
def wallet_withdraw(payload: WalletWithdrawRequest):
    return domain_wallet_withdraw(payload)


@app.get("/api/wallet/logs")
def wallet_logs(user_id: int = Query(1001), page: int = Query(1), size: int = Query(20)):
    return domain_wallet_logs(user_id, page, size)


@app.post("/api/chat/messages")
def send_message(payload: SendMessageRequest):
    return domain_send_message(payload)


@app.get("/api/chat/messages")
def get_messages(order_id: str = Query(), user_id: int = Query(),
                 target_user_id: Optional[int] = Query(None),
                 page: int = Query(1), size: int = Query(50)):
    return domain_get_messages(order_id, user_id, target_user_id, page, size)


@app.put("/api/chat/messages/read")
def mark_read(order_id: str = Query(), user_id: int = Query(),
              target_user_id: Optional[int] = Query(None)):
    return domain_mark_messages_read(order_id, user_id, target_user_id)


@app.post("/api/complaints")
def create_complaint(payload: CreateComplaintRequest):
    return domain_create_complaint(payload)


@app.get("/api/complaints")
def list_complaints(user_id: int = Query(), page: int = Query(1), size: int = Query(20)):
    return domain_list_complaints(user_id, page, size)


@app.get("/api/admin/complaints")
def admin_list_complaints(status: int = Query(None), page: int = Query(1), size: int = Query(20)):
    return domain_admin_list_complaints(status, page, size)


@app.put("/api/admin/complaints/{ticket_id}")
def admin_handle_complaint(ticket_id: int, payload: HandleComplaintRequest):
    return domain_admin_handle_complaint(ticket_id, payload)


@app.get("/api/admin/stats")
def admin_stats():
    return domain_admin_statistics()


@app.get("/api/admin/withdrawals")
def admin_list_withdrawals(page: int = Query(1), size: int = Query(20)):
    return domain_admin_list_withdrawals(page, size)


@app.post("/api/admin/withdrawals/{user_id}/approve")
def admin_approve_withdrawal(user_id: int):
    return domain_admin_approve_withdrawal(user_id)


@app.post("/api/admin/withdrawals/{user_id}/reject")
def admin_reject_withdrawal(user_id: int):
    return domain_admin_reject_withdrawal(user_id)
