-- material_stock_sub: ラベル色（白 / 緑）
ALTER TABLE `material_stock_sub`
  ADD COLUMN `label_color` varchar(20) NULL DEFAULT NULL COMMENT 'ラベル色（白/緑）' AFTER `remarks`;
