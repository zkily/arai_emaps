-- TABLE: fin_expense_application
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_expense_application` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `application_no` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '申請番号',
  `employee_id` int DEFAULT NULL COMMENT '申請者',
  `employee_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '社員名',
  `applied_date` date NOT NULL COMMENT '申請日',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '件名',
  `total_amount` decimal(18,2) DEFAULT '0.00' COMMENT '合計金額',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'draft' COMMENT '状態（下書き/申請中/承認済/却下/支払済）',
  `approver_id` int DEFAULT NULL COMMENT '承認者',
  `approved_at` datetime DEFAULT NULL COMMENT '承認日時',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_expense_application_application_no` (`application_no`),
  KEY `idx_fin_expense_application_employee_id` (`employee_id`),
  KEY `idx_fin_expense_application_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='経費申請';

SET FOREIGN_KEY_CHECKS = 1;
