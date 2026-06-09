-- ============================================================
-- OPS 域测试种子数据（演示用）
-- 注意：测试数据放在 SQL 脚本里，不写在代码中
-- ============================================================

USE ops_db;

-- 清空已有测试数据（幂等执行）
-- DELETE FROM ops_wallet_log;
-- DELETE FROM ops_wallet;
-- DELETE FROM ops_chat_message;
-- DELETE FROM ops_complaint;

-- 钱包：用户1（乘客）初始300，支付35.50后余额264.50
--      用户2（车主）  初始300，收款35.50后余额335.50
--      用户3（车主，有冻结金额用于提现演示）
INSERT INTO ops_wallet (user_id, balance, frozen_amount, status) VALUES
(1, 264.50, 0.00, 1),
(2, 335.50, 0.00, 1),
(3, 280.00, 20.00, 1);

-- 钱包流水：演示数据
INSERT INTO ops_wallet_log (user_id, amount_change, balance_before, balance_after, biz_type, biz_ref_id, idempotency_key, counterparty_id, remark) VALUES
(1, 300.00, 0.00, 300.00, 4, NULL, 'init_recharge_1', NULL, '初始充值'),
(2, 300.00, 0.00, 300.00, 4, NULL, 'init_recharge_2', NULL, '初始充值'),
(1, -35.50, 300.00, 264.50, 1, 10001, 'pay_order_10001', 2, '支付订单 10001'),
(2, 35.50, 300.00, 335.50, 1, 10001, NULL, 1, '收款订单 10001'),
(3, -20.00, 300.00, 280.00, 2, NULL, 'withdraw_demo_3', NULL, '提现申请 20.00');

-- 聊天消息
INSERT INTO ops_chat_message (order_id, sender_id, receiver_id, content, is_read) VALUES
(10001, 1, 2, '你好，明天8点可以吗？', 1),
(10001, 2, 1, '可以，准时到', 1),
(10001, 1, 2, '好的，谢谢！', 0);

-- 投诉工单
INSERT INTO ops_complaint (order_id, plaintiff_id, defendant_id, reason_type, detail, status) VALUES
(10001, 1, 2, 1, '司机迟到 15 分钟，影响行程', 0),
(10002, 2, 1, 3, '乘客取消订单太晚', 1),
(10003, 1, 2, 0, '车内环境较差', 2);
