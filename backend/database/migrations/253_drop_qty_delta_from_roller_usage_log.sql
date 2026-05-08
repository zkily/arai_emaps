-- roller_usage_log から未使用列 qty_delta を削除
ALTER TABLE `roller_usage_log`
  DROP COLUMN `qty_delta`;
