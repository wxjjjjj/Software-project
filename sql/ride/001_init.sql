-- ride_db 订单车辆域数据库
-- Owner: hws（订单核心）+ zj（车辆）
-- 说明：仅由订单车辆域负责人维护，其他域禁止直接修改表结构

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS ride_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ride_db;

-- ─────────────────────────────────────────────
-- 车辆表（zj 负责，hws 只读引用）
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vehicle (
  id            BIGINT       PRIMARY KEY AUTO_INCREMENT,
  owner_user_id VARCHAR(64)  NOT NULL               COMMENT '车主 userId（来自 account_db，仅存 ID）',
  plate_no      VARCHAR(32)  NOT NULL UNIQUE         COMMENT '车牌号',
  brand         VARCHAR(64)                          COMMENT '品牌型号',
  color         VARCHAR(32)                          COMMENT '车辆颜色',
  seat_capacity INT          NOT NULL               COMMENT '总座位数',
  verified      TINYINT(1)  NOT NULL DEFAULT 0      COMMENT '是否已认证',
  status        ENUM('available','disabled') NOT NULL DEFAULT 'available',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_vehicle_owner (owner_user_id)
) COMMENT '车辆信息';

CREATE TABLE IF NOT EXISTS vehicle_verify_request (
  id                 BIGINT       PRIMARY KEY AUTO_INCREMENT,
  vehicle_id         BIGINT       NOT NULL,
  owner_user_id      VARCHAR(64)  NOT NULL,
  owner_name         VARCHAR(64)  NOT NULL,
  id_no              VARCHAR(32)  NOT NULL,
  driver_license_no  VARCHAR(64)  NOT NULL,
  vehicle_license_no VARCHAR(64)  NOT NULL,
  contact_phone      VARCHAR(32),
  remark             VARCHAR(255),
  status             ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  review_note        VARCHAR(255),
  reviewed_by        VARCHAR(64),
  reviewed_at        DATETIME,
  created_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_vehicle_verify_status (status),
  INDEX idx_vehicle_verify_vehicle (vehicle_id)
) COMMENT '车辆认证申请';

-- ─────────────────────────────────────────────
-- 订单主表（hws 负责）
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
  id               VARCHAR(36)    PRIMARY KEY                   COMMENT '订单 UUID',
  passenger_id     VARCHAR(64)    NOT NULL                      COMMENT '发单乘客 userId',
  start_loc        VARCHAR(100)   NOT NULL                      COMMENT '出发地',
  end_loc          VARCHAR(100)   NOT NULL                      COMMENT '目的地',
  depart_time_from DATETIME       NOT NULL                      COMMENT '出发时间窗口起点',
  depart_time_to   DATETIME       NOT NULL                      COMMENT '出发时间窗口终点',
  seats_needed     TINYINT        NOT NULL                      COMMENT '需要的座位总数',
  seats_joined     TINYINT        NOT NULL DEFAULT 1            COMMENT '已参与人数（含发单人）',
  expected_price   DECIMAL(8,2)   NOT NULL                      COMMENT '预期总费用',
  owner_id         VARCHAR(64)    NULL                          COMMENT '接单车主 userId（未接单为 NULL）',
  vehicle_id       VARCHAR(36)    NULL                          COMMENT '接单车辆 ID（未接单为 NULL）',
  locked_time      DATETIME       NULL                          COMMENT '车主接单时间',
  status           ENUM('published','locked','full','completed','cancelled')
                                  NOT NULL DEFAULT 'published'  COMMENT '订单状态',
  created_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_orders_passenger (passenger_id),
  INDEX idx_orders_owner     (owner_id),
  INDEX idx_orders_status    (status),
  INDEX idx_orders_time      (depart_time_from)
) COMMENT '拼车订单主表';

-- ─────────────────────────────────────────────
-- 订单标签表（hws 负责）
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_tag (
  id           VARCHAR(36)  PRIMARY KEY         COMMENT '标签 UUID',
  order_id     VARCHAR(36)  NOT NULL            COMMENT '所属订单 ID',
  tag_content  VARCHAR(30)  NOT NULL            COMMENT '标签内容（如"宠物友好"）',
  INDEX idx_order_tag_order (order_id)
) COMMENT '订单标签';

-- ─────────────────────────────────────────────
-- 订单参与乘客表（hws 负责）
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_passenger (
  id           VARCHAR(36)  PRIMARY KEY         COMMENT '记录 UUID',
  order_id     VARCHAR(36)  NOT NULL            COMMENT '所属订单 ID',
  passenger_id VARCHAR(64)  NOT NULL            COMMENT '参与乘客 userId',
  join_time    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
  pay_status   ENUM('pending','paid','refunded') NOT NULL DEFAULT 'pending' COMMENT '支付状态',
  INDEX idx_op_order      (order_id),
  INDEX idx_op_passenger  (passenger_id),
  UNIQUE KEY uq_order_passenger (order_id, passenger_id)
) COMMENT '订单参与乘客记录';

-- ─────────────────────────────────────────────
-- 订单状态日志表（原框架保留，记录状态流转轨迹）
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_status_log (
  id               BIGINT       PRIMARY KEY AUTO_INCREMENT,
  order_id         VARCHAR(36)  NOT NULL            COMMENT '所属订单 ID',
  from_status      VARCHAR(32)                      COMMENT '流转前状态（初始创建时为 NULL）',
  to_status        VARCHAR(32)  NOT NULL            COMMENT '流转后状态',
  operator_user_id BIGINT                            COMMENT '操作人 userId',
  changed_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_order_status_log_order_id (order_id)
) COMMENT '订单状态变更日志';
