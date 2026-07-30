-- 生産検討会資料（月次 PPT）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_review_meetings` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `target_month` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '対象月 YYYY-MM',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft' COMMENT 'draft/final',
  `data_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ページデータJSON',
  `generated_at` datetime NULL DEFAULT NULL COMMENT '最終集計日時',
  `created_by_user_id` int NULL DEFAULT NULL COMMENT '作成者ID',
  `updated_by_user_id` int NULL DEFAULT NULL COMMENT '更新者ID',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_prm_target_month` (`target_month`),
  KEY `idx_prm_status` (`status`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '生産検討会資料（月次）' ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `production_review_capacity` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程コード',
  `process_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程名',
  `equipment_label` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備・人員表示',
  `standard_rate` int NOT NULL DEFAULT 0 COMMENT '標準能率 本/H',
  `shift_label` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '標準稼働直',
  `working_days` int NOT NULL DEFAULT 0 COMMENT '稼働日数（0=対象月カレンダー）',
  `utilization_rate_pct` decimal(5, 2) NOT NULL DEFAULT 96.00 COMMENT '稼働率(%) 定時H計算用',
  `plan_adjust_rate_pct` decimal(8, 2) NOT NULL DEFAULT 100.00 COMMENT '計画調整率(%) 計画(千本)×調整率',
  `daily_regular_hours` int NOT NULL DEFAULT 0 COMMENT '日当たり定時H',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '表示順',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_prc_process_cd` (`process_cd`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '生産検討会用工程能力' ROW_FORMAT = Dynamic;

INSERT IGNORE INTO production_review_capacity
  (process_cd, process_name, equipment_label, standard_rate, shift_label, daily_regular_hours, sort_order)
VALUES
  ('cutting', '切断', '5.5台', 445, '2直', 8, 1),
  ('chamfering', '面取', '4.5台 (2工程)', 295, '2直', 7, 2),
  ('molding', '成型', '24ライン', 122, '2直', 4, 3),
  ('plating', 'メッキ', '1台', 1620, '3直', 2, 4),
  ('inspection', '検査', '11人', 540, '2直', 8, 5),
  ('welding', '溶接', '6人', 131, '2直', 5, 6),
  ('welding_sp', '溶接SP', '2人', 145, '2直', 2, 7);

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_INVENTORY_PRODUCTION_REVIEW', '生産検討会資料', m.id, '/erp/inventory/production-review', 'Document', 59
FROM menus m
WHERE m.code = 'ERP_INVENTORY'
LIMIT 1;

SET FOREIGN_KEY_CHECKS = 1;
