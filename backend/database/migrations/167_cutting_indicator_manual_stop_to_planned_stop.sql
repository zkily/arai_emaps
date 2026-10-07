-- 切断実績収集登録：手動登録の「停止」を setup_hours（段取）から planned_stop_hours（計画停止時間）へ移行
-- 段取・修理・鋸刃交換を個別入力にしたため、既存の手動データの「停止」を段取と区別する
-- work_hours はどちらも控除対象のため再計算不要
SET NAMES utf8mb4;

UPDATE `cutting_production_indicator`
SET
  `planned_stop_hours` = `setup_hours`,
  `setup_hours` = NULL
WHERE `data_source` = 'manual'
  AND `setup_hours` IS NOT NULL
  AND `planned_stop_hours` IS NULL;
