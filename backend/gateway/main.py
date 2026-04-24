# 后端统一入口，配置三套数据库连接（环境变量等）
# 在每个API处理函数里，替换成 MySQL 读写
# 返回前端需要的字段，不暴露数据库细节。
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import httpx
from backend.common.config import (
    ACCOUNT_SERVICE_URL,
    OPS_SERVICE_URL,
    RIDE_SERVICE_URL,
)

app = FastAPI(title="Rideshare Gateway Skeleton", version="0.1.0", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "gateway"}


async def _forward(request: Request, target_base_url: str) -> Response:
    target_url = f"{target_base_url}{request.url.path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    request_body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient(timeout=30.0) as client:
        upstream_response = await client.request(
            method=request.method,
            url=target_url,
            content=request_body,
            headers=headers,
        )

    response_headers = dict(upstream_response.headers)
    response_headers.pop("content-length", None)
    response_headers.pop("transfer-encoding", None)
    response_headers.pop("connection", None)

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
    )


@app.api_route(
    "/api/auth/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def account_auth_proxy(path: str, request: Request):
    _ = path
    return await _forward(request, ACCOUNT_SERVICE_URL)


@app.api_route(
    "/api/users/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def account_users_proxy(path: str, request: Request):
    _ = path
    return await _forward(request, ACCOUNT_SERVICE_URL)


@app.api_route("/api/admin/login", methods=["POST"])
async def account_admin_login_proxy(request: Request):
    return await _forward(request, ACCOUNT_SERVICE_URL)


@app.api_route(
    "/api/orders/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ride_orders_proxy(path: str, request: Request):
    # Rule: owners cannot publish ride orders.
    # Rule: lock order immediately once accepted.
    _ = path
    return await _forward(request, RIDE_SERVICE_URL)


@app.api_route(
    "/api/orders",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ride_orders_root_proxy(request: Request):
    return await _forward(request, RIDE_SERVICE_URL)


@app.api_route(
    "/api/vehicles/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ride_vehicles_proxy(path: str, request: Request):
    _ = path
    return await _forward(request, RIDE_SERVICE_URL)


@app.api_route(
    "/api/vehicles",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ride_vehicles_root_proxy(request: Request):
    return await _forward(request, RIDE_SERVICE_URL)


@app.api_route(
    "/api/driver/orders/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ride_driver_orders_proxy(path: str, request: Request):
    _ = path
    return await _forward(request, RIDE_SERVICE_URL)


@app.api_route(
    "/api/payments/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ops_payments_proxy(path: str, request: Request):
    _ = path
    return await _forward(request, OPS_SERVICE_URL)


@app.api_route(
    "/api/wallet/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ops_wallet_proxy(path: str, request: Request):
    _ = path
    return await _forward(request, OPS_SERVICE_URL)


@app.api_route(
    "/api/feedback/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ops_feedback_sub_proxy(path: str, request: Request):
    _ = path
    return await _forward(request, OPS_SERVICE_URL)


@app.api_route(
    "/api/feedback",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ops_feedback_root_proxy(request: Request):
    return await _forward(request, OPS_SERVICE_URL)


@app.api_route(
    "/api/admin/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ops_admin_proxy(path: str, request: Request):
    _ = path
    return await _forward(request, OPS_SERVICE_URL)
