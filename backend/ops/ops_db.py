from contextlib import contextmanager

import pymysql

from backend.common.config import (
    OPS_DB_HOST,
    OPS_DB_NAME,
    OPS_DB_PASSWORD,
    OPS_DB_PORT,
    OPS_DB_USER,
)


@contextmanager
def get_ops_conn():
    conn = pymysql.connect(
        host=OPS_DB_HOST,
        port=OPS_DB_PORT,
        user=OPS_DB_USER,
        password=OPS_DB_PASSWORD,
        database=OPS_DB_NAME,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
