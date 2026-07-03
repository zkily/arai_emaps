-- 管理コード → 日内示归属（lot_forecast_attribution）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `lot_forecast_attribution` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード',
  `aps_batch_plan_id` int NULL DEFAULT NULL COMMENT 'APS批次計画ID（lot安定锚点）',
  `instruction_plan_id` int NULL DEFAULT NULL COMMENT 'instruction_plans.id（移行後はNULL可）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '生産計画側品番',
  `canonical_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '等価グループ代表品番（末尾1）',
  `demand_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '需求侧品番（variant）',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '納入先CD',
  `process_key` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程キー',
  `source_date` date NULL DEFAULT NULL COMMENT '工程计划/实绩日',
  `forecast_attribution_date` date NULL DEFAULT NULL COMMENT '内示归属日（客户出货需求日）',
  `attributed_qty` int NOT NULL DEFAULT 0 COMMENT '归属数量',
  `method` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'FIFO_DEMAND' COMMENT 'FIFO_DEMAND/FIFO_OVERFLOW/INVENTORY_PEG/CHAIN_INHERIT/NO_DEMAND',
  `allocation_rule` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'CROSS_DAY_FIFO/SAME_DAY_PROPORTIONAL',
  `attribution_mode` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PLAN' COMMENT 'PLAN/ACTUAL',
  `confidence` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'HIGH' COMMENT 'HIGH/LOW/OVERFLOW',
  `source_entity` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'instruction_plans/cutting_management/chamfering_management',
  `source_entity_id` int NULL DEFAULT NULL COMMENT '来源行ID',
  `run_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '计算批次',
  `is_current` tinyint(1) NOT NULL DEFAULT 1 COMMENT '当前有效版本',
  `computed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '计算时间',
  PRIMARY KEY (`id`),
  INDEX `idx_lfa_canonical_date` (`canonical_product_cd`, `forecast_attribution_date`),
  INDEX `idx_lfa_dest_date` (`destination_cd`, `forecast_attribution_date`),
  INDEX `idx_lfa_aps_current` (`aps_batch_plan_id`, `is_current`),
  INDEX `idx_lfa_mgmt_entity` (`management_code`, `source_entity_id`),
  INDEX `idx_lfa_run_id` (`run_id`),
  INDEX `idx_lfa_product_mode` (`product_cd`, `attribution_mode`, `is_current`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '管理コード日内示归属' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
