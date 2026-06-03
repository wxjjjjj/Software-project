-- ========================================================
-- 初始化测试数据
-- ========================================================

USE account_db;

-- 插入内置管理员 (admin / 123456)
INSERT INTO users (username, password, phone, real_name, id_card, role) 
VALUES ('admin', '123456', '10000000000', '系统管理员', '000000000000000000', 'admin');

-- 插入一个已注册的车主 (yxx / yxx123)
INSERT INTO users (username, password, phone, real_name, id_card, role, passenger_status, driver_status, passenger_score, driver_score) 
VALUES ('yxx', 'yxx123', '18398173617', '王怡心', '510923200502178547', 'driver', 'active', 'approved', 100, 100);

-- 插入一个没有认证的乘客 (111 / 111111)
INSERT INTO users (username, password, phone, real_name, id_card, role, passenger_status, passenger_score) 
VALUES ('111', '111111', '13988889999', '李四', '110101199202025678', 'passenger', 'active', 100);

-- 插入一个用于订单车辆域演示数据的车主 (driver1 / driver1)
INSERT INTO users (id, username, password, phone, real_name, id_card, role, passenger_status, driver_status, passenger_score, driver_score)
VALUES (998, 'driver1', 'driver1', '13800000000', '测试车主', '110101199001011234', 'driver', 'active', 'approved', 100, 100);
