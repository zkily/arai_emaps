-- SEED: numbering_rules
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `numbering_rules` (`id`, `code`, `name`, `prefix`, `format`, `start_number`, `increment`, `current_number`, `reset_type`, `last_reset_date`, `is_active`, `description`) VALUES
(1, 'SALES_ORDER', '受注番号', 'SO', '{PREFIX}-{YYYY}{MM}-{SEQ:4}', 1, 1, 0, 'monthly', NULL, 1, NULL),
(2, 'QUOTATION', '見積番号', 'QT', '{PREFIX}-{YYYY}{MM}{DD}-{SEQ:3}', 1, 1, 0, 'daily', NULL, 1, NULL),
(3, 'PURCHASE_ORDER', '発注番号', 'PO', '{PREFIX}-{YYYY}-{SEQ:5}', 1, 1, 0, 'yearly', NULL, 1, NULL),
(4, 'INVOICE', '請求書番号', 'INV', '{PREFIX}{YYYY}{MM}-{SEQ:4}', 1, 1, 0, 'monthly', NULL, 1, NULL),
(5, 'SHIPMENT', '出荷番号', 'SHP', '{PREFIX}-{YYYY}{MM}{DD}-{SEQ:3}', 1, 1, 0, 'daily', NULL, 1, NULL);

SET FOREIGN_KEY_CHECKS = 1;
