-- 面取バッチ一覧（chamfering_plans）：新規追加時は cutting_management_id を NULL で登録可能にする
SET NAMES utf8mb4;

ALTER TABLE `chamfering_plans`
  MODIFY COLUMN `cutting_management_id` int NULL COMMENT '元切断指示ID（新規追加時はNULL）';
