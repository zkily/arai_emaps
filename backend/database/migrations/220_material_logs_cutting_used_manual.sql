-- material_logs: 現場未ログイン等で切断CSVに無いが実際は使用済の場合、手動で「切断使用済」と扱う
SET NAMES utf8mb4;

ALTER TABLE `material_logs`
  ADD COLUMN `cutting_used_manual` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '手動で切断使用済と確定' AFTER `note`,
  ADD COLUMN `cutting_used_manual_at` DATETIME NULL DEFAULT NULL COMMENT '手動確定日時' AFTER `cutting_used_manual`,
  ADD COLUMN `cutting_used_manual_by` VARCHAR(100) NULL DEFAULT NULL COMMENT '手動確定ユーザー' AFTER `cutting_used_manual_at`,
  ADD COLUMN `cutting_used_manual_note` VARCHAR(500) NULL DEFAULT NULL COMMENT '手動確定理由・備考' AFTER `cutting_used_manual_by`,
  ADD KEY `idx_material_logs_cutting_used_manual` (`cutting_used_manual`);
