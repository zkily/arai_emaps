-- TABLE: inspection_mes_qr_scan
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inspection_mes_qr_scan` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `inspection_id` int DEFAULT NULL COMMENT 'inspection_management.id',
  `production_day` date NOT NULL COMMENT '生産日',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `unit_per_box` int NOT NULL DEFAULT '0' COMMENT '入数（本/箱）',
  `box_qty` int NOT NULL DEFAULT '1' COMMENT '箱数',
  `piece_qty` int NOT NULL DEFAULT '0' COMMENT '本数（入数×箱数）',
  `scanned_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '読取生値（5桁など）',
  `inspector_user_id` int DEFAULT NULL COMMENT '検査員 users.id',
  `registered_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登録時間',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_inspection_id` (`inspection_id`),
  KEY `idx_production_day_product` (`production_day`,`product_cd`),
  KEY `idx_inspector_user_id` (`inspector_user_id`),
  KEY `idx_registered_at` (`registered_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='検査MES QR読取ログ';

SET FOREIGN_KEY_CHECKS = 1;
