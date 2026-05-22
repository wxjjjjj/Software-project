import os
import traceback
from .account_db import get_db_connection
from backend.common.config import ACCOUNT_USE_MOCK

class AccountService:
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
            # yzr: 多角色测试账号（用于 Ride + OPS 联调）
            if username == "admin":
                return {"userId": 1, "username": "admin", "role": "admin", "account_status": "active"}
            if username == "driver1":
                return {"userId": 998, "username": "driver1", "role": "driver", "account_status": "active",
                        "passenger": {"score": 100, "status": "active"},
                        "driver": {"score": 100, "status": "approved"}}
            # --- 关键点：这里必须根据用户名来模拟管理员 ---
            if username == "admin": 
                return {"userId": 1, "username": "admin", "role": "admin", "account_status": "active"}
            return {"userId": 999, "username": username, "role": "passenger", "account_status": "active"}
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
            # 这里的字段必须写全，否则前端收不到状态
            return {
                "id": user_id,
                "username": "yxx",
                "real_name": "测试用户",
                "phone": "13800000000",
                "driver_status": "approved", # 确保 Mock 这里是 approved
                "passenger_score": 100,
                "driver_score": 100
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
        if AccountService.is_mock(): return True
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET driver_status = 'pending' WHERE id = %s", (user_id,))
                sql = "INSERT INTO cars (user_id, license_plate, car_model, car_color) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (user_id, car_data.license_plate, car_data.car_model, car_data.car_color))
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
        if AccountService.is_mock(): return {"items": []}
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id as userId, username, passenger_status, driver_status FROM users")
                return {"items": cursor.fetchall()}
        finally:
            conn.close()

    @staticmethod
    def update_status(user_id, target_identity, new_status):
        if AccountService.is_mock(): return True
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
