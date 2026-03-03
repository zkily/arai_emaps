-- 面取バッチ一覧テーブル（chamfering_plans）：切断指示登録時に面取工程ありの場合に自動登録。面取指示へ移行前に滞留。
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `chamfering_plans`;
CREATE TABLE `chamfering_plans` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `cutting_management_id` int NOT NULL COMMENT '元切断指示ID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `production_order` int NULL DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `actual_production_quantity` int NULL DEFAULT 0 COMMENT '生産数',
  `production_lot_size` int NULL DEFAULT NULL COMMENT 'ロット数',
  `lot_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo',
  `chamfering_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取長',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原材料',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード',
  `cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'CD（管理コード後5位）',
  `production_completed` tinyint NULL DEFAULT NULL COMMENT '生産完了',
  `no_count` tinyint NULL DEFAULT NULL COMMENT 'カウント無',
  `has_sw_process` tinyint NULL DEFAULT NULL COMMENT 'SW工程',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  INDEX `idx_cutting_management_id` (`cutting_management_id`),
  INDEX `idx_production_month` (`production_month`),
  INDEX `idx_production_day` (`production_day`),
  INDEX `idx_production_line` (`production_line`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='面取バッチ一覧（chamfering_plans）';

-- cd フィールド：管理コード後5位をトリガーで自動設定
DROP TRIGGER IF EXISTS `chamfering_plans_cd_before_insert`;
CREATE TRIGGER `chamfering_plans_cd_before_insert`
BEFORE INSERT ON `chamfering_plans`
FOR EACH ROW
SET NEW.`cd` = IF(NEW.`management_code` IS NOT NULL AND TRIM(NEW.`management_code`) != '', RIGHT(NEW.`management_code`, 5), NULL);

DROP TRIGGER IF EXISTS `chamfering_plans_cd_before_update`;
CREATE TRIGGER `chamfering_plans_cd_before_update`
BEFORE UPDATE ON `chamfering_plans`
FOR EACH ROW
SET NEW.`cd` = IF(NEW.`management_code` IS NOT NULL AND TRIM(NEW.`management_code`) != '', RIGHT(NEW.`management_code`, 5), NULL);

SET FOREIGN_KEY_CHECKS = 1;
