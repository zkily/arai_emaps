-- TABLE: factory_layout_objects
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `factory_layout_objects` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `layout_id` int NOT NULL COMMENT 'factory_layouts.id',
  `object_type` varchar(20) NOT NULL COMMENT 'machine / aisle / material_zone',
  `x` int NOT NULL DEFAULT '0' COMMENT '左上 X',
  `y` int NOT NULL DEFAULT '0' COMMENT '左上 Y',
  `width` int NOT NULL DEFAULT '80' COMMENT '幅',
  `height` int NOT NULL DEFAULT '60' COMMENT '高さ',
  `label` varchar(100) NOT NULL DEFAULT '' COMMENT '表示名',
  `ref_cd` varchar(100) DEFAULT NULL COMMENT '設備コードまたは庫位',
  `z_index` int NOT NULL DEFAULT '0' COMMENT '重なり順',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `rotation` int NOT NULL DEFAULT '0' COMMENT '回転角 0/90/180/270',
  `locked` tinyint(1) NOT NULL DEFAULT '0' COMMENT '1=ロック',
  `group_key` varchar(36) DEFAULT NULL COMMENT '同一キーはグループ',
  `fill_color` varchar(7) DEFAULT NULL COMMENT '塗り色 #RRGGBB。NULL は状態色',
  `border_color` varchar(7) DEFAULT NULL COMMENT '枠線色 #RRGGBB',
  `opacity` int NOT NULL DEFAULT '100' COMMENT '不透明度 0-100',
  `child_layout_id` int DEFAULT NULL COMMENT 'このブロックが開く内部レイアウト',
  PRIMARY KEY (`id`),
  KEY `idx_factory_layout_objects_layout` (`layout_id`),
  KEY `idx_factory_layout_objects_child` (`child_layout_id`),
  CONSTRAINT `fk_factory_layout_objects_child` FOREIGN KEY (`child_layout_id`) REFERENCES `factory_layouts` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_factory_layout_objects_layout` FOREIGN KEY (`layout_id`) REFERENCES `factory_layouts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工場レイアウト上のオブジェクト';

SET FOREIGN_KEY_CHECKS = 1;
