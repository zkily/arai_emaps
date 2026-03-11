-- production_summarys に sw_machine（sw機器）カラムを追加（設備フィールド更新で product_machine_config.sw_machine を同期するため）
ALTER TABLE `production_summarys`
  ADD COLUMN `sw_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'sw機器' AFTER `chamfering_machine`;
