from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.ops.ops_domain import FeedbackCreateRequest
from backend.ops.ops_domain import PayOrderRequest
from backend.ops.ops_domain import WalletWithdrawRequest
from backend.ops.ops_domain import (
    admin_list_feedback as ops_admin_list_feedback,
)
from backend.ops.ops_domain import admin_list_orders as ops_admin_list_orders
from backend.ops.ops_domain import admin_list_users as ops_admin_list_users
from backend.ops.ops_domain import create_feedback as ops_create_feedback
from backend.ops.ops_domain import pay_order as ops_pay_order
from backend.ops.ops_domain import wallet_info as ops_wallet_info
from backend.ops.ops_domain import wallet_withdraw as ops_wallet_withdraw

app = FastAPI(title="Ops Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ops"}


@app.post("/api/payments/orders/{order_id}/pay")
def pay_order(order_id: int, payload: PayOrderRequest):
    return ops_pay_order(order_id, payload)


@app.get("/api/wallet/me")
def wallet_info():
    return ops_wallet_info()


@app.post("/api/wallet/withdraw")
def wallet_withdraw(payload: WalletWithdrawRequest):
    return ops_wallet_withdraw(payload)


@app.post("/api/feedback")
def create_feedback(payload: FeedbackCreateRequest):
    return ops_create_feedback(payload)


@app.get("/api/admin/users")
def admin_list_users():
    return ops_admin_list_users()


@app.get("/api/admin/orders")
def admin_list_orders():
    return ops_admin_list_orders()


@app.get("/api/admin/feedback")
def admin_list_feedback():
    return ops_admin_list_feedback()
