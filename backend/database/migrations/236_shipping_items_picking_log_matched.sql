-- shipping_log.picking_no と shipping_no_p が一致するログが存在する場合 1、否则 0
-- PickingLog 取込・ログ削除時にアプリ側で再計算する
--
-- 性能: 相関 EXISTS は shipping_items 行ごとに shipping_log を探しに行きやすい。
--       shipping_log から picking_no を一度だけ集約した派生表と LEFT JOIN する方が、
--       idx_picking_no を活かしやすく大規模データで速くなることが多い。
--       （028_shipping_log.sql の KEY idx_picking_no (picking_no) を前提）

ALTER TABLE shipping_items
  ADD COLUMN picking_log_matched TINYINT(1) NOT NULL DEFAULT 0
    COMMENT 'shipping_log に picking_no=shipping_no_p の行があれば1否则0'
  AFTER status;

-- MySQL 8.0.12+ で列追加のみが INSTANT 対象の場合は、運用で次のようにすると ALTER 自体も短縮できる場合あり:
-- ALTER TABLE shipping_items ADD COLUMN ... ALGORITHM=INSTANT;

UPDATE shipping_items si
LEFT JOIN (
  SELECT picking_no
  FROM shipping_log
  WHERE picking_no IS NOT NULL AND picking_no != ''
  GROUP BY picking_no
) sl ON sl.picking_no = si.shipping_no_p
SET si.picking_log_matched = IF(sl.picking_no IS NULL, 0, 1)
WHERE si.shipping_no_p IS NOT NULL AND si.shipping_no_p != '';
