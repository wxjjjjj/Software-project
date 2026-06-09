import pymysql
import os
from dotenv import load_dotenv

# 这里也保留 load_dotenv 是为了防止你单独测试此文件，但主要靠入口文件加载
load_dotenv()

def get_db_connection():
    # 只有当这个函数被【真正调用】时，才会去连数据库
    # 只要 service.py 里的 if is_mock() 拦截成功，这里就不会运行
    return pymysql.connect(
        host=os.getenv("ACCOUNT_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("ACCOUNT_DB_PORT", 3306)),
        user=os.getenv("ACCOUNT_DB_USER", "root"),
        password=os.getenv("ACCOUNT_DB_PASSWORD", "123456"),
        database=os.getenv("ACCOUNT_DB_NAME", "account_db"),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5 # 设置超时，防止数据库没开时程序卡死很久
    )