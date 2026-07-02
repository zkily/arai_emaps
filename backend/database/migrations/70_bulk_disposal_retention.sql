-- 大量廃棄・保留品 記録管理
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `bulk_disposal_retention_records` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `occurred_date` date NOT NULL COMMENT '発生日',
  `report_category` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '報告区分（大量廃棄/保留品/その他）',
  `process_name` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '発生工程',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品CD',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `quantity` int NOT NULL DEFAULT 0 COMMENT '発生本数',
  `handling_status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '未処理' COMMENT '処理（未処理/処理済）',
  `processed_date` date NULL DEFAULT NULL COMMENT '処理日付',
  `management_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理No',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_by_user_id` int NULL DEFAULT NULL COMMENT '登録者ID',
  `updated_by_user_id` int NULL DEFAULT NULL COMMENT '更新者ID',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  INDEX `idx_bdr_occurred_date` (`occurred_date`),
  INDEX `idx_bdr_handling_status` (`handling_status`),
  INDEX `idx_bdr_report_category` (`report_category`),
  INDEX `idx_bdr_process_name` (`process_name`),
  INDEX `idx_bdr_product_cd` (`product_cd`),
  INDEX `idx_bdr_management_no` (`management_no`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '大量廃棄・保留品記録' ROW_FORMAT = Dynamic;

INSERT INTO notification_settings (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled, is_active)
VALUES
('BULK_DISPOSAL_RETENTION_PENDING', '大量廃棄・保留品 未処理通知', '未処理の大量廃棄・保留品記録を指定担当者へメール通知', 0, 1, 0, 0, 1)
ON DUPLICATE KEY UPDATE event_name = VALUES(event_name), description = VALUES(description);

INSERT INTO email_templates (code, name, subject, body, event_code, language, variables, is_active)
VALUES
(
  'BULK_DISPOSAL_RETENTION_PENDING',
  '大量廃棄・保留品 未処理通知',
  '【Smart-EMAP】未処理 大量廃棄・保留品 {item_count}件',
  '<p>未処理の大量廃棄・保留品記録があります。</p><p>件数: {item_count} 件<br>合計本数: {total_quantity} 本<br>送信者: {sent_by}<br>送信日時: {sent_at}</p>{item_table}<p>Smart-EMAP 在庫管理システム</p>',
  'BULK_DISPOSAL_RETENTION_PENDING',
  'ja',
  '["item_count","total_quantity","item_table","item_list_text","sent_by","sent_at"]',
  1
)
ON DUPLICATE KEY UPDATE name = VALUES(name), subject = VALUES(subject), body = VALUES(body), variables = VALUES(variables);

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_INVENTORY_BULK_DISPOSAL_RETENTION', '大量廃棄・保留品管理', m.id, '/erp/inventory/bulk-disposal-retention', 'WarningFilled', 57
FROM menus m
WHERE m.code = 'ERP_INVENTORY'
LIMIT 1;

SET FOREIGN_KEY_CHECKS = 1;
