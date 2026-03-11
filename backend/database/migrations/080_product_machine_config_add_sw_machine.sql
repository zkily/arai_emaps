-- product_machine_config に sw_machine（sw機器）カラムを追加
ALTER TABLE `product_machine_config`
  ADD COLUMN `sw_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'sw機器' AFTER `chamfering_machine`;
