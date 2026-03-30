-- ride_db仅示例，以自己设计为准
-- 说明：订单车辆域数据库，仅由订单车辆域负责人维护
CREATE DATABASE IF NOT EXISTS ride_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ride_db;

-- 订单主表：维护订单核心信息与主状态流转
CREATE TABLE IF NOT EXISTS ride_order (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  passenger_user_id BIGINT NOT NULL,
  from_text VARCHAR(128) NOT NULL,
  to_text VARCHAR(128) NOT NULL,
  depart_time DATETIME NOT NULL,
  seat_count INT NOT NULL,
  expected_price DECIMAL(10,2) NOT NULL,
  order_status ENUM('CREATED','LOCKED','PASSENGER_CONFIRMED','PAID','COMPLETED','CANCELED') NOT NULL DEFAULT 'CREATED',
  owner_user_id BIGINT,
  vehicle_id BIGINT,
  locked_time DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_ride_order_passenger (passenger_user_id),
  INDEX idx_ride_order_status (order_status)
);

-- 标签字典表：维护可选标签配置
CREATE TABLE IF NOT EXISTS tag_dict (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tag_code VARCHAR(64) NOT NULL UNIQUE,
  tag_name VARCHAR(64) NOT NULL,
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 订单-标签关联表：一笔订单可关联多个标签
CREATE TABLE IF NOT EXISTS order_tag_rel (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  tag_code VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_order_tag_rel_order_id (order_id)
);

-- 车辆表：维护车主车辆信息与可用状态
CREATE TABLE IF NOT EXISTS vehicle (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  owner_user_id BIGINT NOT NULL,
  plate_no VARCHAR(32) NOT NULL UNIQUE,
  brand VARCHAR(64),
  color VARCHAR(32),
  seat_capacity INT NOT NULL,
  verified TINYINT(1) NOT NULL DEFAULT 0,
  status ENUM('available','disabled') NOT NULL DEFAULT 'available',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_vehicle_owner (owner_user_id)
);

-- 订单状态日志表：记录状态流转轨迹
CREATE TABLE IF NOT EXISTS order_status_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  from_status VARCHAR(32),
  to_status VARCHAR(32) NOT NULL,
  operator_user_id BIGINT,
  changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_order_status_log_order_id (order_id)
);
