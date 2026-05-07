-- account_db仅示例，以自己设计为准
-- 说明：账号身份域数据库，仅由账号域负责人维护
CREATE DATABASE IF NOT EXISTS account_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE account_db;

-- 用户主表：统一账号、角色、状态
CREATE TABLE IF NOT EXISTS user_account (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  phone VARCHAR(32),
  real_name VARCHAR(64),
  role_type ENUM('passenger','owner','admin') NOT NULL DEFAULT 'passenger',
  owner_verified TINYINT(1) NOT NULL DEFAULT 0,
  status ENUM('active','disabled') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 车主认证表：保存车主认证申请与审核结果
CREATE TABLE IF NOT EXISTS owner_verification (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  id_card_no VARCHAR(64),
  driver_license_no VARCHAR(64),
  vehicle_license_no VARCHAR(64),
  verify_status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  reject_reason VARCHAR(255),
  submitted_at DATETIME,
  reviewed_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_owner_verification_user_id (user_id)
);

-- 管理员账号表：内置管理员登录信息
CREATE TABLE IF NOT EXISTS admin_account (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  status ENUM('active','disabled') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 已完成车主身份认证的测试账号：用户名 dev-owner，密码 123456
INSERT INTO user_account
  (username, password_hash, phone, real_name, role_type, owner_verified, status)
VALUES
  (
    'dev-owner',
    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
    '13800000001',
    '测试车主',
    'owner',
    1,
    'active'
  )
ON DUPLICATE KEY UPDATE
  password_hash = VALUES(password_hash),
  role_type = 'owner',
  owner_verified = 1,
  status = 'active';

INSERT INTO owner_verification
  (user_id, id_card_no, driver_license_no, vehicle_license_no, verify_status, submitted_at, reviewed_at)
SELECT
  u.id,
  '310101199001011234',
  'DL-DEV-OWNER-001',
  'VL-DEV-OWNER-001',
  'approved',
  NOW(),
  NOW()
FROM user_account u
WHERE u.username = 'dev-owner'
  AND NOT EXISTS (
    SELECT 1 FROM owner_verification ov
    WHERE ov.user_id = u.id AND ov.verify_status = 'approved'
  );
