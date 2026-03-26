-- APS 子表の line_id を production_lines から machines へ切替
-- 先に machines に APS 用列を追加（既存ならエラーになるためそのステートメントをスキップ）

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `machines`
  ADD COLUMN `default_work_hours` DECIMAL(4,2) NULL DEFAULT NULL COMMENT '基準稼働時間（時間）' AFTER `machine_type`;

ALTER TABLE `machines`
  ADD COLUMN `is_active` TINYINT(1) NULL DEFAULT 1 COMMENT '有効フラグ' AFTER `default_work_hours`;

-- 既存 FK 削除（名前は 092/093/094 マイグレーション準拠）
ALTER TABLE `line_capacities` DROP FOREIGN KEY `fk_lc_line`;
ALTER TABLE `production_schedules` DROP FOREIGN KEY `fk_ps_line`;
ALTER TABLE `line_capacity_time_slots` DROP FOREIGN KEY `fk_lcts_line`;
ALTER TABLE `line_product_standard` DROP FOREIGN KEY `fk_lps_line`;

-- production_lines.id → machines.id（line_code = machine_cd で対応）
UPDATE `line_capacities` lc
INNER JOIN `production_lines` pl ON lc.`line_id` = pl.`id`
INNER JOIN `machines` m ON m.`machine_cd` = pl.`line_code`
SET lc.`line_id` = m.`id`;

UPDATE `production_schedules` ps
INNER JOIN `production_lines` pl ON ps.`line_id` = pl.`id`
INNER JOIN `machines` m ON m.`machine_cd` = pl.`line_code`
SET ps.`line_id` = m.`id`;

UPDATE `line_capacity_time_slots` lcts
INNER JOIN `production_lines` pl ON lcts.`line_id` = pl.`id`
INNER JOIN `machines` m ON m.`machine_cd` = pl.`line_code`
SET lcts.`line_id` = m.`id`;

UPDATE `line_product_standard` lps
INNER JOIN `production_lines` pl ON lps.`line_id` = pl.`id`
INNER JOIN `machines` m ON m.`machine_cd` = pl.`line_code`
SET lps.`line_id` = m.`id`;

-- machines に無い参照は削除（整合性のため）
DELETE lc FROM `line_capacities` lc
LEFT JOIN `machines` m ON m.`id` = lc.`line_id`
WHERE m.`id` IS NULL;

DELETE ps FROM `production_schedules` ps
LEFT JOIN `machines` m ON m.`id` = ps.`line_id`
WHERE m.`id` IS NULL;

DELETE lcts FROM `line_capacity_time_slots` lcts
LEFT JOIN `machines` m ON m.`id` = lcts.`line_id`
WHERE m.`id` IS NULL;

DELETE lps FROM `line_product_standard` lps
LEFT JOIN `machines` m ON m.`id` = lps.`line_id`
WHERE m.`id` IS NULL;

-- 新 FK（line_id は machines.id を指す意味で維持）
ALTER TABLE `line_capacities`
  ADD CONSTRAINT `fk_lc_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE;

ALTER TABLE `production_schedules`
  ADD CONSTRAINT `fk_ps_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`);

ALTER TABLE `line_capacity_time_slots`
  ADD CONSTRAINT `fk_lcts_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE;

ALTER TABLE `line_product_standard`
  ADD CONSTRAINT `fk_lps_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE;

SET FOREIGN_KEY_CHECKS = 1;

-- production_lines は参照されなくなったが、履歴用に残す。不要なら手動 DROP 可。
-- DROP TABLE IF EXISTS `production_lines`;
