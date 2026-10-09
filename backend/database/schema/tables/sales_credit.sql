-- TABLE: sales_credit
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `sales_credit` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `customer_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '顧客名',
  `credit_limit` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT '与信限度額',
  `current_balance` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT '現在残高',
  `available_credit` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT '利用可能額',
  `risk_level` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'low' COMMENT 'low/medium/high/blocked',
  `last_review_date` date DEFAULT NULL COMMENT '前回審査日',
  `next_review_date` date DEFAULT NULL COMMENT '次回審査日',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT 'active/suspended/blocked',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sc_customer` (`customer_code`),
  KEY `idx_sc_risk_level` (`risk_level`),
  KEY `idx_sc_status` (`status`),
  KEY `idx_sc_next_review` (`next_review_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='与信管理';

SET FOREIGN_KEY_CHECKS = 1;
