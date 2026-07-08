-- 上段枠1-4の手動固定フラグ
SET NAMES utf8mb4;

ALTER TABLE `product_label_config`
  ADD COLUMN `upper_slots_locked` TINYINT(1) NOT NULL DEFAULT 0
  COMMENT '上段枠1-4手動固定（枠導出時に上書きしない）'
  AFTER `product_name_color`;
