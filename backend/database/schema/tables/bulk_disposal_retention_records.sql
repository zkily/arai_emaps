-- TABLE: bulk_disposal_retention_records
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `bulk_disposal_retention_records` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `occurred_date` date NOT NULL COMMENT '発生日',
  `report_category` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '報告区分（大量廃棄/保留品/その他）',
  `process_name` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '発生工程',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '製品CD',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `quantity` int NOT NULL DEFAULT '0' COMMENT '発生本数',
  `handling_status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '未処理' COMMENT '処理（未処理/処理済）',
  `processed_date` date DEFAULT NULL COMMENT '処理日付',
  `processing_deadline_date` date DEFAULT NULL COMMENT '期間内処理期限（保留品）',
  `management_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '管理No',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_by_user_id` int DEFAULT NULL COMMENT '登録者ID',
  `updated_by_user_id` int DEFAULT NULL COMMENT '更新者ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_bdr_occurred_date` (`occurred_date`),
  KEY `idx_bdr_handling_status` (`handling_status`),
  KEY `idx_bdr_report_category` (`report_category`),
  KEY `idx_bdr_process_name` (`process_name`),
  KEY `idx_bdr_product_cd` (`product_cd`),
  KEY `idx_bdr_management_no` (`management_no`),
  KEY `idx_bdr_processing_deadline` (`processing_deadline_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='大量廃棄・保留品記録';

SET FOREIGN_KEY_CHECKS = 1;
