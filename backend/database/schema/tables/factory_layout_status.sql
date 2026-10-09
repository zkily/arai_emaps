-- TABLE: factory_layout_status
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `factory_layout_status` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `object_id` int NOT NULL COMMENT 'factory_layout_objects.id',
  `status` varchar(30) NOT NULL COMMENT '状態コード',
  `message` varchar(500) DEFAULT NULL COMMENT '説明',
  `payload` json DEFAULT NULL COMMENT '追加情報（PLC 用）',
  `source` varchar(20) NOT NULL DEFAULT 'mock' COMMENT 'mock / plc',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_factory_layout_status_object` (`object_id`),
  CONSTRAINT `fk_factory_layout_status_object` FOREIGN KEY (`object_id`) REFERENCES `factory_layout_objects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工場レイアウトオブジェクトの状態';

SET FOREIGN_KEY_CHECKS = 1;
