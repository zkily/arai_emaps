-- 保留品：期間内処理期限
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `bulk_disposal_retention_records`
  ADD COLUMN `processing_deadline_date` date NULL DEFAULT NULL COMMENT '期間内処理期限（保留品）' AFTER `processed_date`,
  ADD INDEX `idx_bdr_processing_deadline` (`processing_deadline_date`);

SET FOREIGN_KEY_CHECKS = 1;
