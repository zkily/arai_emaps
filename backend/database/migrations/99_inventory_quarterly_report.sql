-- 在庫報告（四半期・半期・年間）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inventory_quarterly_reports` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `fiscal_year` int NOT NULL COMMENT '年度（4月始まり）',
  `quarter` tinyint NOT NULL COMMENT '報告期間 1-4=Q1-Q4, 5=上期4-9, 6=下期10-3, 7=年間4-3',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '報告書タイトル',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft' COMMENT 'draft/final',
  `payload_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '集計スナップショットJSON',
  `scrap_overrides_json` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '廃棄率手動上書きJSON',
  `executive_summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '報告向け要約',
  `action_items` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '改善アクション',
  `notes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `generated_at` datetime NULL DEFAULT NULL COMMENT '集計実行日時',
  `created_by_user_id` int NULL DEFAULT NULL COMMENT '作成者ID',
  `updated_by_user_id` int NULL DEFAULT NULL COMMENT '更新者ID',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_iqr_fy_quarter` (`fiscal_year`, `quarter`),
  INDEX `idx_iqr_status` (`status`),
  INDEX `idx_iqr_fiscal_year` (`fiscal_year`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '在庫報告書（四半期・半期・年間）' ROW_FORMAT = Dynamic;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_INVENTORY_REPORT', '在庫報告管理', m.id, '/erp/inventory/report', 'DataBoard', 58
FROM menus m
WHERE m.code = 'ERP_INVENTORY'
LIMIT 1;

SET FOREIGN_KEY_CHECKS = 1;
