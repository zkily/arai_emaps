-- TABLE: factory_layouts
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `factory_layouts` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `name` varchar(100) NOT NULL COMMENT 'レイアウト名',
  `canvas_width` int NOT NULL DEFAULT '1600' COMMENT 'キャンバス幅',
  `canvas_height` int NOT NULL DEFAULT '900' COMMENT 'キャンバス高さ',
  `grid_size` int NOT NULL DEFAULT '20' COMMENT 'グリッドサイズ',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `kind` varchar(20) NOT NULL DEFAULT 'workshop' COMMENT 'site=総図 / workshop=车间',
  `parent_id` int DEFAULT NULL COMMENT '親レイアウト',
  PRIMARY KEY (`id`),
  KEY `idx_factory_layouts_parent` (`parent_id`),
  CONSTRAINT `fk_factory_layouts_parent` FOREIGN KEY (`parent_id`) REFERENCES `factory_layouts` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工場レイアウト';

SET FOREIGN_KEY_CHECKS = 1;
