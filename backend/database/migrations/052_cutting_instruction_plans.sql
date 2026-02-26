-- 切断指示計画テーブル（指定月でバッチ生成で production_plan_schedules から生成）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `instruction_plans`;
CREATE TABLE `instruction_plans` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `priority_order` int NULL DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `planned_quantity` int NULL DEFAULT 0 COMMENT '計画数',
  `start_date` datetime NULL DEFAULT NULL COMMENT '開始期日',
  `end_date` datetime NULL DEFAULT NULL COMMENT '終了期日',
  `production_lot_size` int NULL DEFAULT NULL COMMENT '生産ロット数',
  `lot_number` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo.',
  `is_cutting_instructed` tinyint(1) NULL DEFAULT 0 COMMENT '切断指示（チェック）',
  `has_chamfering_process` tinyint(1) NULL DEFAULT 0 COMMENT '面取工程（チェック）',
  `is_chamfering_instructed` tinyint(1) NULL DEFAULT 0 COMMENT '面取指示（チェック）',
  `has_sw_process` tinyint(1) NULL DEFAULT 0 COMMENT 'SW工程（チェック）',
  `is_sw_instructed` tinyint(1) NULL DEFAULT 0 COMMENT 'SW指示（チェック）',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード',
  `actual_production_quantity` int NULL DEFAULT 0 COMMENT '生産数',
  `take_count` int NULL DEFAULT NULL COMMENT '取数',
  `cutting_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長',
  `chamfering_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取長',
  `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長',
  `scrap_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '端材長さ（mm）',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原材料',
  `material_manufacturer` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '材料メーカー',
  `standard_specification` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_production_month`(`production_month` ASC) USING BTREE,
  INDEX `idx_product_code`(`product_cd` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '切断指示計画' ROW_FORMAT = Dynamic;

DROP TRIGGER IF EXISTS `tg_generate_management_code`;
delimiter ;;
CREATE TRIGGER `tg_generate_management_code` BEFORE INSERT ON `instruction_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        NEW.product_cd,
        RIGHT(NEW.production_line, 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
