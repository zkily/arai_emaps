-- 設備保全記録に工数(H)を追加
SET NAMES utf8mb4;

ALTER TABLE `quality_equipment_maintenance_records`
  ADD COLUMN `work_hours` DECIMAL(8, 2) NULL COMMENT '工数(H)' AFTER `assignee`;
