from contextlib import contextmanager

import pymysql

from backend.common.config import (
    ACCOUNT_DB_HOST,
    ACCOUNT_DB_NAME,
    ACCOUNT_DB_PASSWORD,
    ACCOUNT_DB_PORT,
    ACCOUNT_DB_USER,
)


@contextmanager
def get_account_conn():
    conn = pymysql.connect(
        host=ACCOUNT_DB_HOST,
        port=ACCOUNT_DB_PORT,
        user=ACCOUNT_DB_USER,
        password=ACCOUNT_DB_PASSWORD,
        database=ACCOUNT_DB_NAME,
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
