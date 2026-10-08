-- 補給品 保管場所マスタ
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `supply_part_locations` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '保管場所名',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '表示順',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '使用フラグ',
  `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '備考',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supply_part_location_name` (`name`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '補給品保管場所マスタ' ROW_FORMAT = Dynamic;

INSERT IGNORE INTO supply_part_locations (name, sort_order)
SELECT DISTINCT storage_location, 0
FROM supply_part_stocks
WHERE storage_location IS NOT NULL AND storage_location <> '';
