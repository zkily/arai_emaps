-- メッキ投入ボード：製品表示を赤字強調するフラグ
SET NAMES utf8mb4;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_board_cards'
    AND COLUMN_NAME = 'text_red'
);

SET @ddl := IF(
  @col_exists = 0,
  'ALTER TABLE aps_plating_plan_board_cards
     ADD COLUMN text_red TINYINT(1) NOT NULL DEFAULT 0
     COMMENT ''ボード上の製品名・数量を赤字で強調表示'' AFTER until_depleted',
  'SELECT 1'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
