-- スケジューリング・設備稼働設定・日別設備計画表・APSロット計画を APS 直下に戻す。
-- 「生産計画作成」配下は成型計画作成（APS_PLANNING）のみとする。

UPDATE menus c
INNER JOIN menus a ON a.code = 'APS'
SET c.parent_id = a.id
WHERE c.code IN (
  'APS_SCHEDULING', 'APS_CAPACITY', 'APS_DAILY_REPORT', 'APS_BATCH_PLANS'
);
