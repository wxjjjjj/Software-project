-- ops_db仅示例，以自己设计为准
-- 说明：交易运营域数据库，仅由交易运营域负责人维护
CREATE DATABASE IF NOT EXISTS ops_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ops_db;

-- 支付订单表：记录订单支付状态
CREATE TABLE IF NOT EXISTS payment_order (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  payer_user_id BIGINT NOT NULL,
  pay_amount DECIMAL(10,2) NOT NULL,
  pay_status ENUM('UNPAID','PAID','REFUNDING','REFUNDED') NOT NULL DEFAULT 'UNPAID',
  paid_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_payment_order_order_id (order_id)
);

-- 钱包账户表：记录车主钱包余额与冻结金额
CREATE TABLE IF NOT EXISTS wallet_account (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  owner_user_id BIGINT NOT NULL UNIQUE,
  balance DECIMAL(12,2) NOT NULL DEFAULT 0,
  frozen_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 钱包流水表：记录收入、提现、退款流水
CREATE TABLE IF NOT EXISTS wallet_txn (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  wallet_id BIGINT NOT NULL,
  txn_type ENUM('income','withdraw','refund') NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  biz_order_id BIGINT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_wallet_txn_wallet_id (wallet_id)
);

-- 提现申请表：记录提现申请与审核状态
CREATE TABLE IF NOT EXISTS withdraw_request (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  owner_user_id BIGINT NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  withdraw_status ENUM('PENDING','APPROVED','REJECTED','CANCELED') NOT NULL DEFAULT 'PENDING',
  requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  finished_at DATETIME,
  INDEX idx_withdraw_request_owner (owner_user_id)
);

-- 反馈主表：用户反馈内容与处理状态
CREATE TABLE IF NOT EXISTS feedback (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  related_order_id BIGINT,
  content VARCHAR(500) NOT NULL,
  feedback_status ENUM('open','processing','closed') NOT NULL DEFAULT 'open',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_feedback_user_id (user_id)
);

-- 反馈回复表：管理员对反馈的回复
CREATE TABLE IF NOT EXISTS feedback_reply (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  feedback_id BIGINT NOT NULL,
  admin_user_id BIGINT NOT NULL,
  reply_content VARCHAR(500) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_feedback_reply_feedback_id (feedback_id)
);

-- 管理员操作日志表：记录后台关键操作
CREATE TABLE IF NOT EXISTS admin_action_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  admin_user_id BIGINT NOT NULL,
  action_type VARCHAR(64) NOT NULL,
  target_type VARCHAR(64) NOT NULL,
  target_id BIGINT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
