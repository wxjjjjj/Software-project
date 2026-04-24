import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("ACCOUNT_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("ACCOUNT_DB_PORT", 3306)),
        user=os.getenv("ACCOUNT_DB_USER", "root"),
        password=os.getenv("ACCOUNT_DB_PASSWORD", "123456"),
        database=os.getenv("ACCOUNT_DB_NAME", "account_db"),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )