import os
from pathlib import Path
from dotenv import load_dotenv

# 显式加载 backend/.env，不依赖启动目录
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://127.0.0.1:8001")
RIDE_SERVICE_URL = os.getenv("RIDE_SERVICE_URL", "http://127.0.0.1:8002")
OPS_SERVICE_URL = os.getenv("OPS_SERVICE_URL", "http://127.0.0.1:8003")

# 供后续接真实数据库时使用的占位配置
ACCOUNT_DB_HOST = os.getenv("ACCOUNT_DB_HOST", "127.0.0.1")
ACCOUNT_DB_PORT = int(os.getenv("ACCOUNT_DB_PORT", "3306"))
ACCOUNT_DB_NAME = os.getenv("ACCOUNT_DB_NAME", "account_db")
ACCOUNT_DB_USER = os.getenv("ACCOUNT_DB_USER", "root")
ACCOUNT_DB_PASSWORD = os.getenv("ACCOUNT_DB_PASSWORD", "")

RIDE_DB_HOST = os.getenv("RIDE_DB_HOST", "127.0.0.1")
RIDE_DB_PORT = int(os.getenv("RIDE_DB_PORT", "3306"))
RIDE_DB_NAME = os.getenv("RIDE_DB_NAME", "ride_db")
RIDE_DB_USER = os.getenv("RIDE_DB_USER", "root")
RIDE_DB_PASSWORD = os.getenv("RIDE_DB_PASSWORD", "")

OPS_DB_HOST = os.getenv("OPS_DB_HOST", "127.0.0.1")
OPS_DB_PORT = int(os.getenv("OPS_DB_PORT", "3306"))
OPS_DB_NAME = os.getenv("OPS_DB_NAME", "ops_db")
OPS_DB_USER = os.getenv("OPS_DB_USER", "root")
OPS_DB_PASSWORD = os.getenv("OPS_DB_PASSWORD", "")

# 供三域在数据库未完成时切换 mock 的开关
ACCOUNT_USE_MOCK = _as_bool(os.getenv("ACCOUNT_USE_MOCK"), default=True)
RIDE_USE_MOCK = _as_bool(os.getenv("RIDE_USE_MOCK"), default=True)
OPS_USE_MOCK = _as_bool(os.getenv("OPS_USE_MOCK"), default=True)
