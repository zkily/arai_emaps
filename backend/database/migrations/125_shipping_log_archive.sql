-- shipping_log の過去データを退避するアーカイブ表。
-- ホットテーブル（shipping_log）は直近 30 日を保持し、突合・CSV 取込は従来どおりそちらを参照する。

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `shipping_log_archive` LIKE `shipping_log`;

ALTER TABLE `shipping_log_archive`
  COMMENT = '出荷ピッキングログ退避（shipping_log から移動）';

DROP PROCEDURE IF EXISTS add_shipping_log_archive_archived_at;

DELIMITER //
CREATE PROCEDURE add_shipping_log_archive_archived_at()
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'shipping_log_archive'
      AND column_name = 'archived_at'
  ) THEN
    ALTER TABLE `shipping_log_archive`
      ADD COLUMN `archived_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        COMMENT 'shipping_log から退避した日時' AFTER `updated_at`,
      ADD KEY `idx_archived_at` (`archived_at`);
  END IF;
END//
DELIMITER ;

CALL add_shipping_log_archive_archived_at();
DROP PROCEDURE add_shipping_log_archive_archived_at;
