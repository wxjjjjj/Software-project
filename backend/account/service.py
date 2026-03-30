from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.account.account_domain import UserLogin, UserRegister
from backend.account.account_domain import admin_login as account_admin_login
from backend.account.account_domain import login_user as account_login_user
from backend.account.account_domain import (
    owner_verification_status as account_owner_verification_status,
)
from backend.account.account_domain import (
    register_user as account_register_user,
)

app = FastAPI(title="Account Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "account"}


@app.post("/api/auth/register")
def register_user(payload: UserRegister):
    return account_register_user(payload)


@app.post("/api/auth/login")
def login_user(payload: UserLogin):
    return account_login_user(payload)


@app.post("/api/admin/login")
def admin_login(payload: UserLogin):
    return account_admin_login(payload)


@app.get("/api/users/me/owner-verification")
def owner_verification(username: str):
    return account_owner_verification_status(username)
