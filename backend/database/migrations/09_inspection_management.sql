-- 検査指示・MES検査実績収集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inspection_management` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `production_sequence` int NULL DEFAULT 0 COMMENT '生産順（同一生産日内）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `actual_production_quantity` int NULL DEFAULT 0 COMMENT '生産数（MES確定）',
  `defect_qty` int NULL DEFAULT 0 COMMENT '不良合計',
  `mes_defect_by_item` json NULL DEFAULT NULL COMMENT 'MES不良内訳 JSON（項目ID→数量）',
  `production_completed_check` tinyint(1) NOT NULL DEFAULT 0 COMMENT '実績確定済',
  `mes_production_started_at` datetime NULL DEFAULT NULL COMMENT 'MES生産開始',
  `mes_production_ended_at` datetime NULL DEFAULT NULL COMMENT 'MES生産終了',
  `mes_net_production_sec` int NULL DEFAULT NULL COMMENT 'MES净生産秒',
  `mes_paused_accum_sec` int NULL DEFAULT NULL COMMENT 'MES一時停止累計秒',
  `mes_production_is_paused` tinyint(1) NULL DEFAULT NULL COMMENT '1=一時停止中,0=稼働中,NULL=未開始/終了',
  `mes_inspector_user_id` int NULL DEFAULT NULL COMMENT 'MES検査員(users.id)',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  INDEX `idx_inspection_production_day` (`production_day`),
  INDEX `idx_inspection_product_cd` (`product_cd`),
  INDEX `idx_inspection_production_month` (`production_month`),
  INDEX `idx_inspection_completed` (`production_completed_check`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '検査指示・MES実績' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
