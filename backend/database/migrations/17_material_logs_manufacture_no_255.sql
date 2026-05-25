-- material_logs.manufacture_no: varchar(100) → 255（長い製造番号・CSV 取込エラー 1406 対策）
SET NAMES utf8mb4;

ALTER TABLE `material_logs`
  MODIFY COLUMN `manufacture_no` varchar(255) DEFAULT NULL COMMENT '製造番号';
