-- 面取指示テーブル（chamfering_management）：切断指示の次工程
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `chamfering_management`;
CREATE TABLE `chamfering_management` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `cutting_management_id` int NULL DEFAULT NULL COMMENT '元切断指示ID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `production_order` int NULL DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `actual_production_quantity` int NULL DEFAULT 0 COMMENT '生産数',
  `chamfering_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取長',
  `production_time` decimal(10, 1) NULL DEFAULT NULL COMMENT '生産時間',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原材料',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード',
  `production_completed_check` tinyint(1) NOT NULL DEFAULT 0 COMMENT '生産完了チェック',
  `cd` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci GENERATED ALWAYS AS (RIGHT(`management_code`, 5)) VIRTUAL COMMENT 'CD(管理コード後5位)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  INDEX `idx_cutting_management_id` (`cutting_management_id`),
  INDEX `idx_production_day` (`production_day`),
  INDEX `idx_product_cd` (`product_cd`),
  INDEX `idx_management_code` (`management_code`),
  INDEX `idx_production_month` (`production_month`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '面取指示' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
