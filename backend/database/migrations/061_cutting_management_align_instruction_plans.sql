-- cutting_management を instruction_plans と同じフィールド構成に揃え、production_day, cutting_machine, cd, production_completed_check を維持
SET NAMES utf8mb4;

-- 1) instruction_plans にあり cutting_management にないカラムを追加
ALTER TABLE `cutting_management`
  ADD COLUMN `priority_order` int NULL DEFAULT NULL COMMENT '順位' AFTER `production_sequence`,
  ADD COLUMN `planned_quantity` int NULL DEFAULT 0 COMMENT '計画数' AFTER `product_name`,
  ADD COLUMN `start_date` datetime NULL DEFAULT NULL COMMENT '開始期日' AFTER `planned_quantity`,
  ADD COLUMN `end_date` datetime NULL DEFAULT NULL COMMENT '終了期日' AFTER `start_date`,
  ADD COLUMN `production_lot_size` int NULL DEFAULT NULL COMMENT '生産ロット数' AFTER `end_date`,
  ADD COLUMN `lot_number` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo.' AFTER `production_lot_size`,
  ADD COLUMN `is_cutting_instructed` tinyint(1) NULL DEFAULT 0 COMMENT '切断指示' AFTER `lot_number`,
  ADD COLUMN `has_chamfering_process` tinyint(1) NULL DEFAULT 0 COMMENT '面取工程' AFTER `is_cutting_instructed`,
  ADD COLUMN `is_chamfering_instructed` tinyint(1) NULL DEFAULT 0 COMMENT '面取指示' AFTER `has_chamfering_process`,
  ADD COLUMN `has_sw_process` tinyint(1) NULL DEFAULT 0 COMMENT 'SW工程' AFTER `is_chamfering_instructed`,
  ADD COLUMN `is_sw_instructed` tinyint(1) NULL DEFAULT 0 COMMENT 'SW指示' AFTER `has_sw_process`,
  ADD COLUMN `take_count` int NULL DEFAULT NULL COMMENT '取数' AFTER `actual_production_quantity`,
  ADD COLUMN `cutting_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長' AFTER `take_count`,
  ADD COLUMN `chamfering_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取長' AFTER `cutting_length`,
  ADD COLUMN `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長' AFTER `chamfering_length`,
  ADD COLUMN `scrap_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '端材長さ(mm)' AFTER `developed_length`,
  ADD COLUMN `material_manufacturer` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '材料メーカー' AFTER `material_name`,
  ADD COLUMN `standard_specification` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格' AFTER `material_manufacturer`,
  ADD COLUMN `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時' AFTER `production_completed_check`,
  ADD COLUMN `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時' AFTER `created_at`;

-- 2) 既存データ: production_order → priority_order
UPDATE `cutting_management` SET `priority_order` = `production_order` WHERE `production_order` IS NOT NULL;

-- 3) 旧カラム削除（instruction_plans にないもの）
ALTER TABLE `cutting_management` DROP COLUMN `production_order`;
ALTER TABLE `cutting_management` DROP COLUMN `production_time`;
