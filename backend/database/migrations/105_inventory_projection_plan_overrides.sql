-- 月末在庫予測：計画合計の手動修正（日別×工程、覆盖层。production_summarys は変更しない）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `inventory_projection_plan_overrides` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `plan_date` date NOT NULL COMMENT '対象日',
  `process_key` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程 key（cutting/molding/plating/outsourced_plating/welding/outsourced_welding）',
  `qty` int NOT NULL COMMENT '手動計画合計（本）',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ippo_date_process` (`plan_date`, `process_key`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '月末在庫予測 計画合計手動修正' ROW_FORMAT = Dynamic;
