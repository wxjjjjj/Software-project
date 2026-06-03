# 交易运营域 API

交易运营域服务端口为 `8003`，通常通过网关 `8000` 访问。所有路径均带 `/api` 前缀。

## 当前职责

- 订单支付与钱包余额维护。
- 钱包提现申请和管理员提现审核。
- 订单聊天消息发送、拉取和已读标记。
- 投诉提交和管理员处理。
- 管理员运营统计。

早期文档中的“反馈”已调整为“投诉”。当前前端不再在个人中心提供“我的反馈”入口；投诉从订单详情或用户资料页进入，用户填写“投诉用户名”、投诉类型和投诉详情。

## 订单支付

`POST /api/payments/orders/{order_id}/pay`

请求：

```json
{
  "payerUserId": 3,
  "payeeUserId": 998,
  "amount": 35.5,
  "idempotencyKey": "pay-ord-001-user-3"
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `payerUserId` | 付款用户 ID |
| `payeeUserId` | 收款用户 ID |
| `amount` | 支付金额，必须大于 0 |
| `idempotencyKey` | 可选幂等键。传入后重复请求会返回已处理结果。 |

响应：

```json
{
  "message": "payment success",
  "orderId": "ord-001",
  "status": "PAID"
}
```

常见错误：

- `400`：金额非法。
- `409`：幂等键对应的支付已处理。

## 钱包信息

`GET /api/wallet/info?user_id=3`

响应：

```json
{
  "balance": 512.5,
  "frozenAmount": 0,
  "currency": "CNY"
}
```

说明：若数据库模式下用户还没有钱包记录，后端会创建一条余额为 `0` 的钱包记录。

## 钱包提现

`POST /api/wallet/withdraw`

请求：

```json
{
  "userId": 998,
  "amount": 100
}
```

响应：

```json
{
  "message": "withdraw request accepted",
  "requestId": 7788
}
```

说明：

- 提现会从可用余额转入冻结金额。
- 管理员审核通过后扣除冻结金额；驳回后返还到余额。

## 钱包流水

`GET /api/wallet/logs?user_id=998&page=1&size=20`

响应：

```json
{
  "items": [
    {
      "logId": 1,
      "amountChange": -35.5,
      "balanceAfter": 477,
      "bizType": 1,
      "createdAt": "2026-06-04T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

## 发送聊天消息

`POST /api/chat/messages`

请求：

```json
{
  "orderId": "ord-001",
  "senderId": 3,
  "receiverId": 998,
  "content": "您好，我已经到上车点附近了。"
}
```

响应：

```json
{
  "message": "sent",
  "msgId": 5001
}
```

约束：

- `senderId` 不能等于 `receiverId`。
- 聊天页面左上角由全局布局根据路由 `meta.backTo` 显示返回箭头。

## 查询聊天消息

`GET /api/chat/messages`

Query：

| 参数 | 说明 |
| --- | --- |
| `order_id` | 订单 ID |
| `user_id` | 当前用户 ID |
| `target_user_id` | 可选，对话另一方用户 ID |
| `page` | 页码，默认 `1` |
| `size` | 每页条数，默认 `50` |

响应：

```json
{
  "items": [
    {
      "msgId": 5001,
      "senderId": 3,
      "receiverId": 998,
      "content": "您好，我已经到上车点附近了。",
      "isRead": 0,
      "createdAt": "2026-06-04T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 50
}
```

当前前端会通过账号域资料接口把用户 ID 转为注册用户名展示。

## 标记消息已读

`PUT /api/chat/messages/read`

Query：

```text
/api/chat/messages/read?order_id=ord-001&user_id=3&target_user_id=998
```

响应：

```json
{
  "message": "marked as read",
  "count": 3
}
```

## 提交投诉

`POST /api/complaints`

请求：

```json
{
  "orderId": "ord-001",
  "plaintiffId": 3,
  "defendantId": 998,
  "reasonType": 1,
  "detail": "投诉用户名：driver1\n投诉类型：行程纠纷\n对方未按约定时间到达。",
  "evidenceUrls": ""
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `orderId` | 可选。若从订单详情进入，前端会自动带入；表单不要求用户手填订单编号。 |
| `plaintiffId` | 投诉人用户 ID |
| `defendantId` | 可选。若用户输入的是数字 ID，前端会作为 `defendantId` 传入；若输入注册用户名，则用户名会写入 `detail`。 |
| `reasonType` | 投诉类型：`1` 行程纠纷，`2` 安全问题，`3` 费用问题，`4` 服务态度，`0` 其他 |
| `detail` | 投诉详情，当前会包含“投诉用户名”和投诉类型文本 |
| `evidenceUrls` | 可选证据链接字符串 |

响应：

```json
{
  "message": "complaint submitted",
  "ticketId": 7001
}
```

当前产品设计：

- 个人中心不再单独放“我的反馈”入口。
- 投诉推荐从用户资料页或订单详情进入，减少用户手填无关信息。
- 管理员后台统一查看和处理投诉。

## 查询我的投诉

`GET /api/complaints?user_id=3&page=1&size=20`

说明：后端仍保留该接口，但当前前端不再提供“我的反馈/我的投诉”独立页面。

## 管理员投诉列表

`GET /api/admin/complaints?status=0&page=1&size=20`

Query：

| 参数 | 说明 |
| --- | --- |
| `status` | 可选。`0` 待处理，`1` 已处理，`2` 已驳回或关闭，具体含义以后端数据为准。 |
| `page` | 页码 |
| `size` | 每页条数 |

响应：

```json
{
  "items": [
    {
      "ticketId": 7001,
      "orderId": "ord-001",
      "plaintiffId": 3,
      "defendantId": 998,
      "reasonType": 1,
      "detail": "投诉用户名：driver1\n投诉类型：行程纠纷\n对方未按约定时间到达。",
      "status": 0,
      "adminReply": "",
      "createdAt": "2026-06-04T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

管理员页面会尽量展示被投诉用户名；若无法解析，则展示投诉详情中的用户名或用户 ID。

## 管理员处理投诉

`PUT /api/admin/complaints/{ticket_id}`

请求：

```json
{
  "adminId": 1,
  "status": 1,
  "adminReply": "已核实并完成处理。"
}
```

响应：

```json
{
  "message": "complaint handled",
  "ticketId": 7001
}
```

## 管理员统计

`GET /api/admin/stats`

响应：

```json
{
  "totalWalletCount": 10,
  "totalPaymentAmount": 50000,
  "totalComplaintCount": 3,
  "totalChatMessageCount": 20
}
```

## 管理员提现列表

`GET /api/admin/withdrawals?page=1&size=20`

响应：

```json
{
  "items": [
    {
      "walletId": 1,
      "userId": 998,
      "balance": 500,
      "frozenAmount": 100
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

当前管理员投诉页同时展示待处理投诉和提现申请工作区。

## 管理员审核提现

通过：

```text
POST /api/admin/withdrawals/{user_id}/approve
```

驳回：

```text
POST /api/admin/withdrawals/{user_id}/reject
```

响应：

```json
{
  "message": "withdrawal approved",
  "userId": 998
}
```

## Mock 与数据库模式

- `OPS_USE_MOCK=true`：返回固定 Mock 数据，适合无数据库联调。
- `OPS_USE_MOCK=false`：连接 `ops_db` 真实读写。
- 数据库模式需要先执行 `sql/ops/001_init.sql`。
