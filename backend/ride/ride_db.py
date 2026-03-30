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
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
