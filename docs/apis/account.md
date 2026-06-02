# 账号域 API 文档 (Account Domain)

**负责人: wyx**
服务端口: 8001 (通过 8000 网关访问)

---

### 用户注册

* **方法: POST**
* **路径:** **/api/auth/register**
* **请求 JSON:**

JSON

```
{
  "username": "alice",
  "password": "password123",
  "phone": "13812345678",
  "real_name": "张三",
  "id_card": "110101199001011234"
}
```

* **响应 JSON:**

JSON

```
{
  "message": "register success",
  "userId": 1,
  "username": "alice"
}
```

* **错误码:**

  * **400: 参数格式非法（如手机号不是11位）**
  * **409: 用户名、手机号或身份证已存在**
  * **500: 数据库连接或SQL异常**

---

### 用户登录 (普通用户/车主)

* **方法: POST**
* **路径:** **/api/auth/login**
* **请求 JSON:**

JSON

```
{
  "username": "alice",
  "password": "password123"
}
```

* **响应 JSON:**

JSON

```
{
  "userId": 1,
  "username": "alice",
  "role": "passenger",
  "account_status": "active",
  "passenger": { "score": 100, "status": "active" },
  "driver": { "score": 100, "status": "unapplied" },
  "token": "token-1"
}
```

* **错误码:**

  * **401: 用户名或密码错误**
  * **403: 账号已被整体封禁**
  * **404: 用户不存在**

---

### 管理员登录

* **方法: POST**
* **路径:** **/api/admin/login**
* **说明: 专门适配网关 /api/admin/login 转发规则，仅限数据库 role='admin' 用户。**
* **请求 JSON:**

JSON

```
{
  "username": "admin",
  "password": "admin_password"
}
```

* **响应 JSON:**

JSON

```
{
  "userId": 99,
  "username": "admin",
  "role": "admin",
  "token": "admin-token-99"
}
```

* **错误码:**

  * **401: 账号非管理员或密码错误**

---

### 获取个人详细资料

* **方法: GET**
* **路径:** **/api/users/profile/{user\_id}**
* **响应 JSON:**

JSON

```
{
  "id": 1,
  "username": "alice",
  "phone": "13812345678",
  "real_name": "张三",
  "id_card": "110101199001011234",
  "passenger_score": 100,
  "passenger_status": "active",
  "driver_score": 100,
  "driver_status": "approved",
  "role": "driver"
}
```

* **错误码:**

  * **404: 用户不存在**

---

### 提交车主认证申请

* **方法: POST**
* **路径:** **/api/users/driver/apply/{user\_id}**
* **说明: 提交首辆车信息，将 driver\_status 修改为 pending。**
* **请求 JSON:**

JSON

```
{
  "license_plate": "沪A88888",
  "car_model": "特斯拉 Model 3",
  "car_color": "黑色"
}
```

* **响应 JSON:**

JSON

```
{
  "message": "申请已提交"
}
```

* **错误码:**

  * **400: 申请失败（如已是车主或资料不全）**

---

### [管理员] 获取全量用户列表

* **方法: GET**
* **路径:** **/api/users/admin/users**
* **说明: 避开网关 /api/admin 拦截规则，用于管理后台展示。**
* **响应 JSON:**

JSON

```
{
  "items": [
    {
      "userId": 1,
      "username": "alice",
      "passenger_status": "active",
      "driver_status": "pending"
    }
  ]
}
```

---

### [管理员] 独立修改身份状态 (封禁/解封)

* **方法: POST**
* **路径:** **/api/users/admin/update-status**
* **请求 JSON:**

JSON

```
{
  "userId": 1,
  "target_identity": "driver",
  "new_status": "banned"
}
```

* **响应 JSON:**

JSON

```
{
  "message": "状态已更新"
}
```

* **错误码:**

  * **400: 更新失败**

---

### [跨域调用] 信誉分加减更新

* **方法: POST**
* **路径:** **/api/users/score/update**
* **说明: 供订单域（Ride）行程结束加分或违约扣分调用。**
* **请求 JSON:**

JSON

```
{
  "userId": 1,
  "role_type": "passenger",
  "score_change": -5
}
```

* **响应 JSON:**

JSON

```
{
  "new_score": 95
}
```
