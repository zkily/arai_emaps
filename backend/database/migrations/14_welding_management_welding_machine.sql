-- 溶接設備（MES溶接実績収集・設備マスタ名称を保存）
SET NAMES utf8mb4;

ALTER TABLE `welding_management`
  ADD COLUMN `welding_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '溶接設備名' AFTER `product_name`;

CREATE INDEX `idx_welding_machine_day` ON `welding_management` (`production_day`, `welding_machine`);
