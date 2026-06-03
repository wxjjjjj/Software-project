-- ========================================================
-- 账号域初始化脚本 (Account Domain Initialization)
-- 负责人: wyx
-- ========================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS account_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE account_db;

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

    -- 乘客身份属性
    passenger_score INT DEFAULT 100,
    passenger_status VARCHAR(20) DEFAULT 'active',

    -- 车主身份属性
    driver_score INT DEFAULT 100,
    driver_status VARCHAR(20) DEFAULT 'unapplied', -- unapplied, pending, approved, banned
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

