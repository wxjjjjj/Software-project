-- ============================================================
-- 交易运营域数据库（ops_db）— yzr 设计
-- 共 4 表：ops_wallet / ops_wallet_log / ops_chat_message / ops_complaint
-- ============================================================

CREATE DATABASE IF NOT EXISTS ops_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ops_db;

-- ============================================================
-- 1. 钱包主表
-- ============================================================
CREATE TABLE IF NOT EXISTS ops_wallet (
  wallet_id     BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id       BIGINT NOT NULL UNIQUE,
  balance       DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  frozen_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  status        TINYINT NOT NULL DEFAULT 1 COMMENT '1=正常 0=冻结 2=已注销',
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_wallet_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. 账务流水表（统一记录支付/提现/退款/充值）
-- ============================================================
CREATE TABLE IF NOT EXISTS ops_wallet_log (
  log_id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id         BIGINT NOT NULL,
  amount_change   DECIMAL(12,2) NOT NULL COMMENT '+收入 / -支出',
  balance_before  DECIMAL(12,2) NOT NULL,
  balance_after   DECIMAL(12,2) NOT NULL,
  biz_type        TINYINT NOT NULL COMMENT '1=支付 2=提现 3=退款 4=充值',
  biz_ref_id      VARCHAR(128) DEFAULT NULL COMMENT '业务关联ID（order_id等）',
  idempotency_key VARCHAR(128) DEFAULT NULL UNIQUE COMMENT '幂等键',
  status          TINYINT NOT NULL DEFAULT 1 COMMENT '1=成功 0=失败',
  counterparty_id BIGINT DEFAULT NULL COMMENT '对手方用户ID',
  remark          VARCHAR(255) DEFAULT NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_log_user (user_id),
  INDEX idx_log_biz_ref (biz_type, biz_ref_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. 司乘聊天消息表
-- ============================================================
CREATE TABLE IF NOT EXISTS ops_chat_message (
  msg_id      BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id    VARCHAR(64) NOT NULL,
  sender_id   BIGINT NOT NULL,
  receiver_id BIGINT NOT NULL,
  content     VARCHAR(2000) NOT NULL,
  is_read     TINYINT NOT NULL DEFAULT 0 COMMENT '0=未读 1=已读',
  send_time   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_chat_order (order_id),
  INDEX idx_chat_users (sender_id, receiver_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. 投诉反馈工单表
-- ============================================================
CREATE TABLE IF NOT EXISTS ops_complaint (
  ticket_id     BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id      VARCHAR(64) DEFAULT NULL,
  plaintiff_id  BIGINT NOT NULL COMMENT '投诉人',
  defendant_id  BIGINT DEFAULT NULL COMMENT '被投诉人',
  reason_type   TINYINT NOT NULL DEFAULT 0 COMMENT '0=其他 1=行程纠纷 2=安全问题 3=费用问题 4=服务态度',
  detail        VARCHAR(2000) NOT NULL,
  evidence_urls VARCHAR(1000) DEFAULT NULL COMMENT '图片URL，逗号分隔',
  status        TINYINT NOT NULL DEFAULT 0 COMMENT '0=待处理 1=处理中 2=已解决 3=已驳回',
  admin_id      BIGINT DEFAULT NULL COMMENT '处理管理员ID',
  admin_reply   VARCHAR(1000) DEFAULT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_complaint_plaintiff (plaintiff_id),
  INDEX idx_complaint_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
