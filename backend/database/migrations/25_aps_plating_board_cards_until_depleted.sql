-- メッキ投入ボード治具枠：数量非表示（無くなり次第）フラグ
-- 表示は「無くなり次第」とし、生産数合計には実数を加算する
SET NAMES utf8mb4;

SET @col_exists := (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_board_cards'
    AND COLUMN_NAME = 'until_depleted'
);

SET @ddl := IF(
  @col_exists = 0,
  'ALTER TABLE aps_plating_plan_board_cards
     ADD COLUMN until_depleted TINYINT(1) NOT NULL DEFAULT 0
     COMMENT ''数量非表示（無くなり次第）；合計には実数を加算'' AFTER stable_key',
  'SELECT 1'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
