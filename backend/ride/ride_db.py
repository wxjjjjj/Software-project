from contextlib import contextmanager

import pymysql

from backend.common.config import (
    RIDE_DB_HOST,
    RIDE_DB_NAME,
    RIDE_DB_PASSWORD,
    RIDE_DB_PORT,
    RIDE_DB_USER,
)


@contextmanager
def get_ride_conn():
    conn = pymysql.connect(
        host=RIDE_DB_HOST,
        port=RIDE_DB_PORT,
        user=RIDE_DB_USER,
        password=RIDE_DB_PASSWORD,
        database=RIDE_DB_NAME,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as _c:
            _c.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
