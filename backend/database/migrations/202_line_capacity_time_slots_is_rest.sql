-- 稼働時間帯に「休憩」フラグを追加。is_rest=1 の区間は稼働合算・排産から除く。

SET NAMES utf8mb4;

ALTER TABLE `line_capacity_time_slots`
  ADD COLUMN `is_rest` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1=休憩（稼働から除く）' AFTER `sort_order`;
