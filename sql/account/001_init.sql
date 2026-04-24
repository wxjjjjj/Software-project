-- ========================================================
-- 账号域初始化脚本 (Account Domain Initialization)
-- 负责人: wyx
-- ========================================================

-- 1. 清理旧表 (开发阶段方便重置环境，注意外键顺序)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS cars;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- 2. 创建用户表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    phone VARCHAR(11) UNIQUE NOT NULL,       -- 新增：手机号 (11位)
    real_name VARCHAR(20) NOT NULL,          -- 真实姓名
    id_card VARCHAR(18) UNIQUE NOT NULL,     -- 身份证号 (18位)
    
    -- 基础角色与整体状态
    role VARCHAR(20) DEFAULT 'passenger',    -- passenger, driver, admin
    account_status VARCHAR(20) DEFAULT 'active', -- active, banned

    -- 拼车人身份属性
    passenger_score INT DEFAULT 100,
    passenger_status VARCHAR(20) DEFAULT 'active',

    -- 车主身份属性
    driver_score INT DEFAULT 100,
    driver_status VARCHAR(20) DEFAULT 'unapplied', -- unapplied, pending, approved, banned
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 创建车辆表
CREATE TABLE cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    license_plate VARCHAR(20) NOT NULL,
    car_model VARCHAR(50),
    car_color VARCHAR(20),
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================================================
-- 4. 初始化测试数据 
-- ========================================================

-- 插入内置管理员 (admin / 123456)
INSERT INTO users (username, password, phone, real_name, id_card, role) 
VALUES ('admin', '123456', '10000000000', '系统管理员', '000000000000000000', 'admin');

-- 插入一个已注册的车主 (yxx / yxx123)
INSERT INTO users (username, password, phone, real_name, id_card, role, passenger_status, driver_status, passenger_score, driver_score) 
VALUES ('yxx', 'yxx123', '18398173617', '王怡心', '510923200502178547', 'driver', 'active', 'approved', 100, 100);

-- 插入一个已认证的车主 (driver_test / 123456)
INSERT INTO users (username, password, phone, real_name, id_card, role, driver_status, driver_score) 
VALUES ('111', '111111', '13988889999', '李四', '110101199202025678', 'driver', 'approved', 98);

-- 为该车主绑定一辆已通过审核的车辆
INSERT INTO cars (user_id, license_plate, car_model, car_color, is_approved)
VALUES (2, '沪A88888', '特斯拉 Model 3', '白色', TRUE);