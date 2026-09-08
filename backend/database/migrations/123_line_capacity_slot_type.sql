-- 稼働時間帯に用途区分（稼働 / 休憩 / 技術使用 / 保全）と備考を追加。
-- 技術・保全は休憩と同様に稼働合算・排産から除外し、指示画面で区別表示する。

SET NAMES utf8mb4;

ALTER TABLE `line_capacity_time_slots`
  ADD COLUMN `slot_type` VARCHAR(20) NOT NULL DEFAULT 'work'
    COMMENT 'work=稼働 / rest=休憩 / tech=技術使用 / maintenance=保全'
    AFTER `is_rest`;

ALTER TABLE `line_capacity_time_slots`
  ADD COLUMN `note` VARCHAR(255) NULL
    COMMENT '用途メモ（例: 技術部トライ）'
    AFTER `slot_type`;

-- 既存の休憩行を slot_type=rest に揃える
UPDATE `line_capacity_time_slots`
SET `slot_type` = 'rest'
WHERE COALESCE(`is_rest`, 0) = 1
  AND (`slot_type` IS NULL OR `slot_type` = '' OR `slot_type` = 'work');
