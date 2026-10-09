-- TABLE: chamfering_management
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `chamfering_management` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `cutting_management_id` int DEFAULT NULL COMMENT '元切断指示ID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `chamfering_machine` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '面取機（手動指定）',
  `production_sequence` int DEFAULT '0' COMMENT '生産順',
  `production_order` int DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `actual_production_quantity` int DEFAULT '0' COMMENT '生産数',
  `defect_qty` int DEFAULT '0' COMMENT '不良数',
  `production_lot_size` int DEFAULT NULL COMMENT 'ロット数',
  `lot_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ロットNo',
  `cutting_length` decimal(10,2) DEFAULT NULL COMMENT '切断長',
  `chamfering_length` decimal(10,2) DEFAULT NULL COMMENT '面取長',
  `developed_length` decimal(10,2) DEFAULT NULL COMMENT '展開長',
  `production_time` decimal(10,1) DEFAULT NULL COMMENT '生産時間',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `mes_production_started_at` datetime DEFAULT NULL COMMENT 'MES面取実績収集・生産開始日時',
  `mes_production_ended_at` datetime DEFAULT NULL COMMENT 'MES面取実績収集・生産終了日時',
  `mes_net_production_sec` int DEFAULT NULL COMMENT 'MES净生産秒数(一時停止除く,段取除く)',
  `mes_paused_accum_sec` int DEFAULT NULL COMMENT 'MES一時停止累計秒数',
  `mes_production_is_paused` tinyint(1) DEFAULT NULL COMMENT 'MES稼働計測:1=一時停止中,0=稼働中,NULL=未開始/終了済',
  `mes_setup_time_min` int DEFAULT NULL COMMENT 'MES段取時間(分)',
  `mes_operator_user_id` int DEFAULT NULL COMMENT 'MES作業者(users.id)',
  `mes_scanned_code` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'MES面取実績・バーコード/QR読取',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '原材料',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '管理コード',
  `has_sw_process` tinyint DEFAULT NULL COMMENT 'SW工程',
  `production_completed_check` tinyint(1) NOT NULL DEFAULT '0' COMMENT '生産完了チェック',
  `no_count` tinyint DEFAULT NULL COMMENT 'カウント無',
  `cd` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci GENERATED ALWAYS AS (right(`management_code`,5)) VIRTUAL COMMENT 'CD(管理コード後5位)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_cutting_management_id` (`cutting_management_id`),
  KEY `idx_production_day` (`production_day`),
  KEY `idx_product_cd` (`product_cd`),
  KEY `idx_management_code` (`management_code`),
  KEY `idx_production_month` (`production_month`),
  KEY `idx_chamfering_machine` (`chamfering_machine`),
  CONSTRAINT `fk_chamfering_cutting` FOREIGN KEY (`cutting_management_id`) REFERENCES `cutting_management` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='面取指示';

SET FOREIGN_KEY_CHECKS = 1;
