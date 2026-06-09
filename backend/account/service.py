import os
import traceback
from .account_db import get_db_connection
from backend.common.config import ACCOUNT_USE_MOCK

class AccountService:
    MOCK_USERS = {
        "admin": {
            "password": "123456",
            "user": {
                "userId": 1,
                "username": "admin",
                "real_name": "系统管理员",
                "phone": "10000000000",
                "id_card": "000000000000000000",
                "role": "admin",
                "account_status": "active",
                "passenger": {"score": 100, "status": "active"},
                "driver": {"score": 100, "status": "unapplied"},
            },
        },
        "yxx": {
            "password": "yxx123",
            "user": {
                "userId": 2,
                "username": "yxx",
                "real_name": "王怡心",
                "phone": "18398173617",
                "id_card": "510923200502178547",
                "role": "driver",
                "account_status": "active",
                "passenger": {"score": 100, "status": "active"},
                "driver": {"score": 100, "status": "approved"},
            },
        },
        "111": {
            "password": "111111",
            "user": {
                "userId": 3,
                "username": "111",
                "real_name": "李四",
                "phone": "13988889999",
                "id_card": "110101199202025678",
                "role": "passenger",
                "account_status": "active",
                "passenger": {"score": 100, "status": "active"},
                "driver": {"score": 100, "status": "unapplied"},
            },
        },
        "driver1": {
            "password": "driver1",
            "user": {
                "userId": 998,
                "username": "driver1",
                "real_name": "测试车主",
                "phone": "13800000000",
                "id_card": "110101199001011234",
                "role": "driver",
                "account_status": "active",
                "passenger": {"score": 100, "status": "active"},
                "driver": {"score": 100, "status": "approved"},
            },
        },
    }

    @staticmethod
    def _mock_users_as_list():
        items = []
        for mock_user in AccountService.MOCK_USERS.values():
            user = mock_user["user"]
            items.append({
                "userId": user["userId"],
                "username": user["username"],
                "passenger_status": user.get("passenger", {}).get("status", "active"),
                "driver_status": user.get("driver", {}).get("status", "unapplied"),
            })
        items.sort(key=lambda item: item["userId"])
        return {"items": items}

    @staticmethod
    def _find_mock_user_by_id(user_id):
        user_id_text = str(user_id)
        for mock_user in AccountService.MOCK_USERS.values():
            user = mock_user["user"]
            if str(user.get("userId")) == user_id_text:
                return user
        return None

    @staticmethod
    def is_mock():
        # 读取变量并去掉空格、转小写
        mock_val = os.getenv("ACCOUNT_USE_MOCK")
        if mock_val is None:
            return ACCOUNT_USE_MOCK
        mock_val = mock_val.strip().lower()
        # 调试信息：启动后在控制台看看这个值到底是什么
        # print(f"DEBUG: Current MOCK status is: {mock_val}") 
        return mock_val == "true"

    @staticmethod
    def authenticate_user(username, password):
        if AccountService.is_mock():
            print(f"DEBUG: MOCK模式验证用户 {username}")
            mock_user = AccountService.MOCK_USERS.get(username)
            if not mock_user or mock_user["password"] != password:
                return None
            return mock_user["user"].copy()
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM users WHERE username = %s AND password = %s"
                cursor.execute(sql, (username, password))
                user = cursor.fetchone()
                if user:
                    return {
                        "userId": user["id"],
                        "username": user["username"],
                        "role": user["role"],
                        "account_status": user["account_status"],
                        "passenger": {"score": user["passenger_score"], "status": user["passenger_status"]},
                        "driver": {"score": user["driver_score"], "status": user["driver_status"]}
                    }
                return None
        finally:
            conn.close()

    @staticmethod
    def register_user(data):
        if AccountService.is_mock(): return 888
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """INSERT INTO users (username, password, phone, real_name, id_card, role) 
                         VALUES (%s, %s, %s, %s, %s, 'passenger')"""
                cursor.execute(sql, (data.username, data.password, data.phone, data.real_name, data.id_card))
                conn.commit()
                return cursor.lastrowid
        except Exception:
            conn.rollback()
            traceback.print_exc()
            return None
        finally:
            conn.close()

    @staticmethod
    def get_user_profile(user_id):
        if AccountService.is_mock():
            user = AccountService._find_mock_user_by_id(user_id)
            if not user:
                return None
            return {
                "id": user_id,
                "username": user.get("username"),
                "real_name": user.get("real_name", user.get("username", "")),
                "phone": user.get("phone", ""),
                "id_card": user.get("id_card", ""),
                "account_status": user.get("account_status", "active"),
                "driver_status": user.get("driver", {}).get("status", "unapplied"),
                "passenger_score": user.get("passenger", {}).get("score", 100),
                "driver_score": user.get("driver", {}).get("score", 100),
            }

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 确保数据库查询也包含了 driver_status
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def submit_driver_application(user_id, car_data):
        if AccountService.is_mock():
            user = AccountService._find_mock_user_by_id(user_id)
            if not user:
                return False
            user.setdefault("driver", {})["status"] = "pending"
            user["driver_application"] = {
                "real_name": car_data.real_name,
                "id_card": car_data.id_card,
                "driver_license_no": car_data.driver_license_no,
                "contact_phone": car_data.contact_phone,
                "remark": car_data.remark,
            }
            return True
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, driver_status FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user:
                    return False
                if user.get("driver_status") in ("approved", "active"):
                    return True
                cursor.execute("UPDATE users SET driver_status = 'pending' WHERE id = %s", (user_id,))
                conn.commit()
                return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def get_user_cars(user_id):
        if AccountService.is_mock(): return []
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM cars WHERE user_id = %s", (user_id,))
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_all_users():
        if AccountService.is_mock():
            return AccountService._mock_users_as_list()
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id as userId, username, passenger_status, driver_status FROM users")
                return {"items": cursor.fetchall()}
        finally:
            conn.close()

    @staticmethod
    def update_status(user_id, target_identity, new_status):
        if AccountService.is_mock():
            for mock_user in AccountService.MOCK_USERS.values():
                user = mock_user["user"]
                if user["userId"] != user_id:
                    continue
                if target_identity == "passenger":
                    user.setdefault("passenger", {})["status"] = new_status
                else:
                    user.setdefault("driver", {})["status"] = new_status
                return True
            return False
        conn = get_db_connection()
        try:
            column = "passenger_status" if target_identity == "passenger" else "driver_status"
            with conn.cursor() as cursor:
                sql = f"UPDATE users SET {column} = %s WHERE id = %s"
                cursor.execute(sql, (new_status, user_id))
                conn.commit()
                return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    # 请把这个方法加在 service.py 的 AccountService 类里面（update_status 之后）
    @staticmethod
    def modify_score(user_id, role_type, score_change):
        if AccountService.is_mock():
            return {"new_score": 95}
        conn = get_db_connection()
        try:
            column = "passenger_score" if role_type == "passenger" else "driver_score"
            status_col = "passenger_status" if role_type == "passenger" else "driver_status"
            
            with conn.cursor() as cursor:
                # 1. 执行分数加减
                sql = f"UPDATE users SET {column} = {column} + %s WHERE id = %s"
                cursor.execute(sql, (score_change, user_id))
                
                # 2. 查询最新分数
                cursor.execute(f"SELECT {column} FROM users WHERE id = %s", (user_id,))
                user_data = cursor.fetchone()
                new_score = user_data[column]
                
                # 3. [核心逻辑] 自动封禁：如果分数低于 60 分，自动改为 banned
                if new_score < 60:
                    cursor.execute(f"UPDATE users SET {status_col} = 'banned' WHERE id = %s", (user_id,))
                # 如果分数回升到 60 以上，可以自动解封（可选）
                elif new_score >= 60:
                    cursor.execute(f"UPDATE users SET {status_col} = 'active' WHERE id = %s", (user_id,))
                
                conn.commit()
                return {"new_score": new_score}
        except Exception:
            conn.rollback()
            return None
        finally:
            conn.close()
