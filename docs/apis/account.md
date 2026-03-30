# 账号域API

wyx

数据库: account_db

功能范围: 用户注册登录、车主认证、管理员登录、用户状态

## 集成环境
- 统一地址: http://<wxj主机>:8000
- 接口前缀: /api
- 约束规则: 其他域不得跨库访问 account_db，只能通过HTTP API调用

## 必需接口【仅一点点示例，根据自己的设计修改即可】

### 用户注册
- 方法: POST
- 路径: /api/auth/register
- 请求 JSON:
```json
{
  "username": "alice",
  "password": "pass123"
}
```
- 响应 JSON:
```json
{
  "message": "register success",
  "username": "alice",
  "defaultRole": "passenger"
}
```
- 错误码: 400（参数非法）, 409（用户名已存在）

### 用户登录
- 方法: POST
- 路径: /api/auth/login
- 请求 JSON:
```json
{
  "username": "alice",
  "password": "pass123"
}
```
- 响应 JSON:
```json
{
  "message": "login success",
  "token": "jwt-or-dev-token",
  "role": "user",
  "ownerVerified": false,
  "username": "alice"
}
```
- 错误码: 401（密码错误）, 404（用户不存在）

### 管理员登录
- 方法: POST
- 路径: /api/admin/login
- 请求 JSON:
```json
{
  "username": "admin",
  "password": "admin123"
}
```
- 响应 JSON:
```json
{
  "message": "admin login success",
  "token": "jwt-or-dev-token",
  "role": "admin",
  "username": "admin"
}
```
- 错误码: 401, 403

### 车主认证状态查询
- 方法: GET
- 路径: /api/users/me/owner-verification
- 响应 JSON:
```json
{
  "userId": 1001,
  "ownerVerified": true,
  "verifyStatus": "approved"
}
```
- 错误码: 401

## 其他
