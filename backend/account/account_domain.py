from pydantic import BaseModel
from fastapi import HTTPException
import hashlib

from backend.account.account_db import get_account_conn
from backend.common.config import ACCOUNT_USE_MOCK


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    password: str


def _hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def _build_user_login_response(row: dict) -> dict:
    role_type = row.get("role_type", "passenger")
    response_role = "admin" if role_type == "admin" else "user"
    owner_verified = bool(row.get("owner_verified", 0))
    return {
        "message": "login success",
        "token": f"dev-token-{row.get('id', 'user')}",
        "role": response_role,
        "ownerVerified": owner_verified,
        "username": row["username"],
    }


def register_user(payload: UserRegister) -> dict:
    if ACCOUNT_USE_MOCK:
        return {
            "message": "register success",
            "username": payload.username,
            "defaultRole": "passenger",
        }

    password_hash = _hash_password(payload.password)
    try:
        with get_account_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM user_account WHERE username=%s",
                    (payload.username,),
                )
                exists = cursor.fetchone()
                if exists:
                    raise HTTPException(
                        status_code=409,
                        detail="username already exists",
                    )

                cursor.execute(
                    (
                        "INSERT INTO user_account "
                        "(username, password_hash, role_type, "
                        "owner_verified, status) "
                        "VALUES (%s, %s, 'passenger', 0, 'active')"
                    ),
                    (payload.username, password_hash),
                )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"account db error: {exc}",
        ) from exc

    return {
        "message": "register success",
        "username": payload.username,
        "defaultRole": "passenger",
    }


def login_user(payload: UserLogin) -> dict:
    if ACCOUNT_USE_MOCK:
        return {
            "message": "login success",
            "token": "dev-token-user",
            "role": "user",
            "ownerVerified": False,
            "username": payload.username,
        }

    password_hash = _hash_password(payload.password)
    try:
        with get_account_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    (
                        "SELECT id, username, role_type, owner_verified, "
                        "password_hash, status "
                        "FROM user_account WHERE username=%s"
                    ),
                    (payload.username,),
                )
                row = cursor.fetchone()
                if not row:
                    raise HTTPException(
                        status_code=404,
                        detail="user not found",
                    )
                if row["status"] != "active":
                    raise HTTPException(
                        status_code=403,
                        detail="user is disabled",
                    )
                if row["password_hash"] != password_hash:
                    raise HTTPException(
                        status_code=401,
                        detail="wrong password",
                    )
                return _build_user_login_response(row)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"account db error: {exc}",
        ) from exc

    return {
        "message": "login success",
        "token": "dev-token-user",
        "role": "user",
        "ownerVerified": False,
        "username": payload.username,
    }


def admin_login(payload: UserLogin) -> dict:
    if ACCOUNT_USE_MOCK:
        return {
            "message": "admin login success",
            "token": "dev-token-admin",
            "role": "admin",
            "username": payload.username,
        }

    password_hash = _hash_password(payload.password)
    try:
        with get_account_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    (
                        "SELECT id, username, password_hash, status "
                        "FROM admin_account WHERE username=%s"
                    ),
                    (payload.username,),
                )
                row = cursor.fetchone()
                if not row:
                    raise HTTPException(
                        status_code=404,
                        detail="admin not found",
                    )
                if row["status"] != "active":
                    raise HTTPException(
                        status_code=403,
                        detail="admin is disabled",
                    )
                if row["password_hash"] != password_hash:
                    raise HTTPException(
                        status_code=401,
                        detail="wrong password",
                    )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"account db error: {exc}",
        ) from exc

    return {
        "message": "admin login success",
        "token": "dev-token-admin",
        "role": "admin",
        "username": payload.username,
    }


def owner_verification_status(username: str) -> dict:
    if ACCOUNT_USE_MOCK:
        return {
            "userId": 1001,
            "ownerVerified": True,
            "verifyStatus": "approved",
        }

    try:
        with get_account_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    (
                        "SELECT id, owner_verified FROM user_account "
                        "WHERE username=%s"
                    ),
                    (username,),
                )
                user_row = cursor.fetchone()
                if not user_row:
                    raise HTTPException(
                        status_code=404,
                        detail="user not found",
                    )

                verify_status = "pending"
                cursor.execute(
                    (
                        "SELECT verify_status FROM owner_verification "
                        "WHERE user_id=%s ORDER BY id DESC LIMIT 1"
                    ),
                    (user_row["id"],),
                )
                verify_row = cursor.fetchone()
                if verify_row and verify_row.get("verify_status"):
                    verify_status = verify_row["verify_status"]

                return {
                    "userId": user_row["id"],
                    "ownerVerified": bool(user_row["owner_verified"]),
                    "verifyStatus": verify_status,
                }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"account db error: {exc}",
        ) from exc
