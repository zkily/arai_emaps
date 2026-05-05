ALTER TABLE machines
  ADD COLUMN available_qty INT NULL DEFAULT 0 COMMENT '可用数量' AFTER efficiency;
