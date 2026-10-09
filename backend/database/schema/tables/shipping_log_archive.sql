-- TABLE: shipping_log_archive
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `shipping_log_archive` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '',
  `date` date DEFAULT NULL,
  `datetime` datetime DEFAULT NULL,
  `model_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '',
  `person_in_charge` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '',
  `picking_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '',
  `product_name` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '',
  `product_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '',
  `product_name_2` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '',
  `quantity` int DEFAULT '0',
  `shipping_quantity` int DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `archived_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'shipping_log から退避した日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_picking_product_date` (`picking_no`,`product_code`,`date`),
  KEY `idx_date` (`date`),
  KEY `idx_picking_no` (`picking_no`),
  KEY `idx_archived_at` (`archived_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='出荷ピッキングログ退避（shipping_log から移動）';

SET FOREIGN_KEY_CHECKS = 1;
