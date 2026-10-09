-- TABLE: inspection_management
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inspection_management` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `production_sequence` int DEFAULT '0' COMMENT '生産順（同一生産日内）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `actual_production_quantity` int DEFAULT '0' COMMENT '生産数（MES確定）',
  `defect_qty` int DEFAULT '0' COMMENT '不良合計',
  `mes_defect_by_item` json DEFAULT NULL COMMENT 'MES不良内訳 JSON（項目ID→数量）',
  `mes_scanned_code` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'MES検査実績・バーコード/QR読取',
  `production_completed_check` tinyint(1) NOT NULL DEFAULT '0' COMMENT '実績確定済',
  `mes_production_started_at` datetime DEFAULT NULL COMMENT 'MES生産開始',
  `mes_production_ended_at` datetime DEFAULT NULL COMMENT 'MES生産終了',
  `mes_net_production_sec` int DEFAULT NULL COMMENT 'MES净生産秒',
  `mes_paused_accum_sec` int DEFAULT NULL COMMENT 'MES一時停止累計秒',
  `mes_shift_sec` int DEFAULT NULL COMMENT 'CSVシフト秒',
  `mes_break_sec` int DEFAULT NULL COMMENT 'CSV休憩秒',
  `mes_stop_sec` int DEFAULT NULL COMMENT 'CSV停止(段替等)秒',
  `mes_production_is_paused` tinyint(1) DEFAULT NULL COMMENT '1=一時停止中,0=稼働中,NULL=未開始/終了',
  `mes_inspector_user_id` int DEFAULT NULL COMMENT 'MES検査員(users.id)',
  `mes_client_instance_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'MES操作端末ID（localStorage UUID）',
  `mes_client_lock_activity_at` datetime DEFAULT NULL COMMENT 'MES端末ロック最終アクティビティ（checkpoint・ロック取得時更新）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `manual_registration_note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '実績収集登録備考',
  `external_sync_key` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '外部Excel同期キー（内容ハッシュ・重複防止）',
  `data_source` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'mes' COMMENT '取得元: mes=検査実績収集, excel=管理指標Excel同期, csv=一括取込',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_inspection_external_sync_key` (`external_sync_key`),
  KEY `idx_inspection_production_day` (`production_day`),
  KEY `idx_inspection_product_cd` (`product_cd`),
  KEY `idx_inspection_production_month` (`production_month`),
  KEY `idx_inspection_completed` (`production_completed_check`),
  KEY `idx_inspection_data_source` (`data_source`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='検査指示・MES実績';

SET FOREIGN_KEY_CHECKS = 1;
