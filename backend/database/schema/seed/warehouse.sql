-- SEED: warehouse
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `warehouse` (`id`, `warehouse_code`, `warehouse_name`, `warehouse_type`, `address`, `manager`, `phone`, `capacity`, `is_active`, `remarks`) VALUES
(1, 'WH001', '本社倉庫', 'product', NULL, NULL, NULL, NULL, 1, NULL),
(2, 'WH002', '原材料倉庫', 'material', NULL, NULL, NULL, NULL, 1, NULL),
(3, 'WH003', '出荷センター', 'product', NULL, NULL, NULL, NULL, 1, NULL);

SET FOREIGN_KEY_CHECKS = 1;
