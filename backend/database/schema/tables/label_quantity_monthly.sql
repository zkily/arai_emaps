-- TABLE: label_quantity_monthly
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `label_quantity_monthly` (
  `id` int NOT NULL AUTO_INCREMENT,
  `year_month` char(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '対象月 YYYY-MM',
  `label_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'molding / product_use',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `opening_stock` int NOT NULL DEFAULT '0' COMMENT '月初在庫枚数',
  `opening_locked` tinyint(1) NOT NULL DEFAULT '0' COMMENT '月初在庫手動ロック（1=再計算で上書きしない）',
  `issue_qty` int NOT NULL DEFAULT '0' COMMENT '発行予定(紙枚数)（CEIL(max(0,必要−発行済)/6)、1紙=6枚）',
  `issued_qty` int NOT NULL DEFAULT '0' COMMENT '発行済枚数（印刷実績の累計）',
  `last_issue_history` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '最終発行・印刷履歴',
  `updated_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_label_qty_month_type_cd` (`year_month`,`label_type`,`product_cd`),
  KEY `idx_label_qty_year_month` (`year_month`),
  KEY `idx_label_qty_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ラベル枚数管理（月度）';

SET FOREIGN_KEY_CHECKS = 1;
