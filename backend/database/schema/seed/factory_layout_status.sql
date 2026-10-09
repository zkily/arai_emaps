-- SEED: factory_layout_status
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `factory_layout_status` (`id`, `object_id`, `status`, `message`, `payload`, `source`) VALUES
(1, 1, 'running', '生産中', NULL, 'mock'),
(2, 2, 'idle', '待機', NULL, 'mock'),
(3, 3, 'alarm', '温度異常（模擬）', NULL, 'mock'),
(4, 4, 'open', '通行可', NULL, 'mock'),
(5, 5, 'stocked', '鋼材在庫', NULL, 'mock');

SET FOREIGN_KEY_CHECKS = 1;
