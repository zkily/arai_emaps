-- 設備マスタ：効率（%）の値を可動率（%）へ移し、効率列を削除
SET NAMES utf8mb4;

-- 1) 可動率が未作成なら追加（181 未適用環境向け）
SET @avail_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'machines'
    AND COLUMN_NAME = 'availability_rate'
);

SET @sql := IF(
  @avail_exists = 0,
  'ALTER TABLE `machines` ADD COLUMN `availability_rate` decimal(4, 1) NULL DEFAULT 100.0 COMMENT ''可動率（%）'' AFTER `efficiency`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2) 効率の値を可動率へ反映（小数第1位）
SET @eff_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'machines'
    AND COLUMN_NAME = 'efficiency'
);

SET @sql := IF(
  @eff_exists > 0,
  'UPDATE `machines` SET `availability_rate` = ROUND(`efficiency`, 1) WHERE `efficiency` IS NOT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3) 効率列を削除
SET @sql := IF(
  @eff_exists > 0,
  'ALTER TABLE `machines` DROP COLUMN `efficiency`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
