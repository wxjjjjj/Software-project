#!/bin/bash
# 运营域冒烟测试（Linux版）
BASE_URL="${1:-http://127.0.0.1:8003}"
PASS=0
FAIL=0

check() {
  local name="$1"
  local method="$2"
  local url="$3"
  local body="$4"
  echo -n "[$method] $name ... "
  if [ -n "$body" ]; then
    resp=$(curl -s -X "$method" "$url" -H "Content-Type: application/json" -d "$body" 2>&1)
  else
    resp=$(curl -s -X "$method" "$url" 2>&1)
  fi
  if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d)" 2>/dev/null; then
    echo "OK"
    PASS=$((PASS+1))
  else
    echo "FAIL: $resp"
    FAIL=$((FAIL+1))
  fi
}

echo "=== 运营域冒烟测试（直连 $BASE_URL）==="
echo ""

# 1. 健康检查
check "健康检查" "GET" "$BASE_URL/health" ""

# 2. 钱包信息
check "钱包 info user=1" "GET" "$BASE_URL/api/wallet/info?user_id=1" ""
check "钱包 info user=2" "GET" "$BASE_URL/api/wallet/info?user_id=2" ""

# 3. 支付
IDEM_KEY="smoke_$(date +%s)"
check "订单支付" "POST" "$BASE_URL/api/payments/orders/10001/pay" \
  "{\"payerUserId\":1,\"payeeUserId\":2,\"amount\":35.5,\"idempotencyKey\":\"$IDEM_KEY\"}"

# 4. 幂等重放
check "幂等重放" "POST" "$BASE_URL/api/payments/orders/10001/pay" \
  "{\"payerUserId\":1,\"payeeUserId\":2,\"amount\":35.5,\"idempotencyKey\":\"$IDEM_KEY\"}"

# 5. 流水查询
check "钱包流水 user=1" "GET" "$BASE_URL/api/wallet/logs?user_id=1&page=1&size=20" ""

# 6. 提现
check "钱包提现" "POST" "$BASE_URL/api/wallet/withdraw" \
  "{\"userId\":1,\"amount\":10.0}"

# 7. 发送消息
check "发送消息" "POST" "$BASE_URL/api/chat/messages" \
  "{\"orderId\":10001,\"senderId\":1,\"receiverId\":2,\"content\":\"冒烟测试\"}"

# 8. 获取聊天记录
check "获取消息" "GET" "$BASE_URL/api/chat/messages?order_id=10001&user_id=1" ""

# 9. 标记已读
check "标记已读" "PUT" "$BASE_URL/api/chat/messages/read?order_id=10001&user_id=2" ""

# 10. 提交投诉
check "提交投诉" "POST" "$BASE_URL/api/complaints" \
  "{\"orderId\":10001,\"plaintiffId\":1,\"defendantId\":2,\"reasonType\":1,\"detail\":\"冒烟测试投诉\"}"

# 11. 查看投诉
check "查看投诉 user=1" "GET" "$BASE_URL/api/complaints?user_id=1" ""

# 12. 管理员处理
check "管理员处理" "PUT" "$BASE_URL/api/admin/complaints/1" \
  "{\"adminId\":999,\"status\":2,\"adminReply\":\"已处理\"}"

# 13. 管理员列表
check "管理员投诉列表" "GET" "$BASE_URL/api/admin/complaints" ""

# 14. 运营统计
check "运营统计" "GET" "$BASE_URL/api/admin/stats" ""

echo ""
echo "=== 结果: $PASS 通过, $FAIL 失败 ==="
