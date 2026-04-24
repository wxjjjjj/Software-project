"""
账号域入口文件 (Account Domain Entry Point) - 最终定稿版
负责人：wyx
功能：用户/管理员身份隔离、车主认证、信誉分维护
"""
import re
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from .service import AccountService  # 确保 service.py 中已补全 modify_score 方法

app = FastAPI(title="手机私家车拼车软件-账号域")

# 1. 设置路由前缀为 /api，匹配网关 (8000) 转发规则
router = APIRouter(prefix="/api", tags=["Account"])

# ==========================================
# --- 1. 数据模型定义 (Schemas) ---
# ==========================================

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6)
    phone: str = Field(..., example="13812345678")
    real_name: str
    id_card: str = Field(..., example="110101199001011234")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v

    @field_validator('id_card')
    @classmethod
    def validate_id_card(cls, v):
        if not re.match(r'^\d{17}[\dX]$', v):
            raise ValueError('身份证格式不正确')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class DriverApply(BaseModel):
    license_plate: str
    car_model: str
    car_color: str

class StatusUpdate(BaseModel):
    userId: int
    target_identity: str # "passenger" 或 "driver"
    new_status: str      # "active" 或 "banned"

# ==========================================
# --- 2. 路由接口实现 ---
# ==========================================

# [注册] 路径：/api/auth/register
@router.post("/auth/register", summary="用户注册")
async def register(data: UserRegister):
    result = AccountService.register_user(data)
    if not result:
        raise HTTPException(status_code=409, detail="注册失败：用户名/手机/身份证已存在")
    return {"message": "register success", "userId": result}

# [用户登录] 路径：/api/auth/login
@router.post("/auth/login", summary="普通用户登录")
async def login(data: UserLogin):
    user = AccountService.authenticate_user(data.username, data.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # --- 【强制拦截】禁止管理员从普通入口登录 ---
    print(f"[Login Check] 用户: {user.get('username')}, 角色: {user.get('role')}")
    if user.get("role") == "admin":
        print("[Intercept] 拦截成功：拒绝管理员从普通入口进入")
        raise HTTPException(status_code=403, detail="管理员请从【管理员入口】登录")
    
    if user.get("account_status") == "banned":
        raise HTTPException(status_code=403, detail="账号已被整体封禁")
        
    return user

# [管理员登录] 路径：/api/admin/login
@router.post("/admin/login", summary="管理员专用登录")
async def admin_login(data: UserLogin):
    user = AccountService.authenticate_user(data.username, data.password)
    
    # 严格校验：必须存在且角色必须是 admin
    if not user or user.get("role") != "admin":
        print(f"[Admin Check] 非法尝试：用户 {data.username} 尝试进入管理员入口")
        raise HTTPException(status_code=401, detail="非管理员账号，请从用户入口登录")
    
    print(f"[Admin Login] 管理员 {data.username} 登录成功")
    return user

# [个人资料] 路径：/api/users/profile/{user_id}
@router.get("/users/profile/{user_id}", summary="获取个人资料")
async def get_profile(user_id: int):
    profile = AccountService.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    return profile

# [车主申请] 路径：/api/users/driver/apply/{user_id}
@router.post("/users/driver/apply/{user_id}", summary="车主认证申请")
async def apply_driver(user_id: int, car_data: DriverApply):
    success = AccountService.submit_driver_application(user_id, car_data)
    if not success:
        raise HTTPException(status_code=400, detail="申请失败")
    return {"message": "申请已提交"}

# [查询名下车辆] 路径：/api/users/driver/cars/{user_id}
@router.get("/users/driver/cars/{user_id}", summary="获取名下车辆")
async def get_my_cars(user_id: int):
    return AccountService.get_user_cars(user_id)

# [管理员-用户列表] 路径：/api/users/admin/users
@router.get("/users/admin/users", summary="所有用户列表 (管理员)")
async def list_users():
    return AccountService.get_all_users()

# [管理员-封禁操作] 路径：/api/users/admin/update-status
@router.post("/users/admin/update-status", summary="手动封禁/解封身份")
async def update_identity_status(data: StatusUpdate):
    success = AccountService.update_status(data.userId, data.target_identity, data.new_status)
    if not success:
        raise HTTPException(status_code=400, detail="状态更新失败")
    return {"message": "状态已更新"}

# [跨域加减分] 路径：/api/users/score/update
@router.post("/users/score/update", summary="信誉分更新 (跨域调用)")
async def update_score(userId: int, role_type: str, score_change: int):
    return AccountService.modify_score(userId, role_type, score_change)

# 3. 将路由注册到 app 实例
app.include_router(router)