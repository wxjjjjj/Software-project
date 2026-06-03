-- ride_db 测试种子数据
-- 与 backend/ride/ride_domain.py 中的 Mock 数据保持一致
-- 用途：可选演示/白盒测试数据。真实业务数据库不需要导入本脚本。
-- 执行前提：已执行 001_init.sql

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ride_db;

-- ─────────────────────────────────────────────
-- 车辆（对应 _VEHICLES mock 数据）
-- owner_user_id 使用账号域测试用户 ID：2=yxx，3=111，998=driver1
-- ─────────────────────────────────────────────
INSERT INTO vehicle (id, owner_user_id, plate_no, brand, color, seat_capacity, verified, status) VALUES
  (1, '998', '粤A·88888', '丰田 凯美瑞', '珍珠白', 5, 1, 'available'),
  (2, '2',   '粤B·12345', '本田 雅阁',   '深空黑', 5, 1, 'available'),
  (3, '2',   '粤C·67890', '大众 帕萨特', '银色',   5, 1, 'available');

-- ─────────────────────────────────────────────
-- 订单主表（对应 _ORDERS mock 数据）
-- ─────────────────────────────────────────────
INSERT INTO orders (id, passenger_id, start_loc, end_loc,
                    depart_time_from, depart_time_to,
                    seats_needed, seats_joined, expected_price,
                    owner_id, vehicle_id, locked_time,
                    status, created_at, updated_at) VALUES
  ('ord-seed-001', '3', '软件园',   '大学城',
   '2026-04-15 08:00:00', '2026-04-15 09:00:00',
   3, 1, 45.00, NULL, NULL, NULL,
   'published', '2026-04-13 10:00:00', '2026-04-13 10:00:00'),

  ('ord-seed-002', '2', '天河客运站', '广州南站',
   '2026-04-16 14:00:00', '2026-04-16 15:00:00',
   2, 1, 60.00, NULL, NULL, NULL,
   'published', '2026-04-13 09:00:00', '2026-04-13 09:00:00'),

  ('ord-seed-003', '3', '珠江新城', '广州白云机场',
   '2026-04-17 06:00:00', '2026-04-17 07:00:00',
   3, 3, 80.00, '998', '1', '2026-04-13 12:00:00',
   'locked', '2026-04-13 08:00:00', '2026-04-13 12:00:00'),

  ('ord-seed-004', '2', '南门', '广州南站',
   '2026-04-18 10:00:00', '2026-04-18 11:00:00',
   2, 1, 25.00, NULL, NULL, NULL,
   'published', '2026-04-13 11:00:00', '2026-04-13 11:00:00');

-- ─────────────────────────────────────────────
-- 订单标签（对应 _TAGS mock 数据）
-- ─────────────────────────────────────────────
INSERT INTO order_tag (id, order_id, tag_content) VALUES
  ('tag-s1', 'ord-seed-001', '静音'),
  ('tag-s2', 'ord-seed-001', '禁烟'),
  ('tag-s3', 'ord-seed-002', '宠物友好'),
  ('tag-s4', 'ord-seed-003', '早高峰'),
  ('tag-s5', 'ord-seed-003', '不绕路'),
  ('tag-s6', 'ord-seed-004', '准时出发'),
  ('tag-s7', 'ord-seed-004', '禁烟');

-- ─────────────────────────────────────────────
-- 订单参与乘客（对应 _PASSENGERS mock 数据）
-- ─────────────────────────────────────────────
INSERT INTO order_passenger (id, order_id, passenger_id, join_time, pay_status) VALUES
  ('rec-s1', 'ord-seed-001', '3',   '2026-04-13 10:00:00', 'pending'),
  ('rec-s2', 'ord-seed-002', '2',   '2026-04-13 09:00:00', 'pending'),
  ('rec-s3', 'ord-seed-003', '3',   '2026-04-13 08:00:00', 'pending'),
  ('rec-s4', 'ord-seed-003', '2',   '2026-04-13 08:30:00', 'pending'),
  ('rec-s5', 'ord-seed-003', '998', '2026-04-13 09:00:00', 'pending');

-- ─────────────────────────────────────────────
-- 状态日志（覆盖 ord-seed-003 的完整流转轨迹）
-- ─────────────────────────────────────────────
INSERT INTO order_status_log (order_id, from_status, to_status, operator_user_id, changed_at) VALUES
  ('ord-seed-003', NULL,        'published', NULL, '2026-04-13 08:00:00'),
  ('ord-seed-003', 'published', 'locked',    NULL, '2026-04-13 12:00:00');
-- operator_user_id 为 BIGINT，演示数据此处留 NULL；真实业务数据由服务写入操作人 ID
