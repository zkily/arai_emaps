-- TABLE: fin_attendance_record
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_attendance_record` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `employee_id` int DEFAULT NULL COMMENT '社員',
  `employee_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '社員名',
  `work_date` date NOT NULL COMMENT '勤務日',
  `clock_in` datetime DEFAULT NULL COMMENT '出勤',
  `clock_out` datetime DEFAULT NULL COMMENT '退勤',
  `break_minutes` int DEFAULT '0' COMMENT '休憩分',
  `work_minutes` int DEFAULT '0' COMMENT '実働分',
  `overtime_minutes` int DEFAULT '0' COMMENT '残業分',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'normal' COMMENT '状態（正常/遅刻/欠勤/休暇）',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_attendance_record_employee_id` (`employee_id`),
  KEY `idx_fin_attendance_record_work_date` (`work_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='勤怠記録';

SET FOREIGN_KEY_CHECKS = 1;
