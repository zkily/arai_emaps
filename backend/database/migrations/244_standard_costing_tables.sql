-- 標準原価マスタ・月次実績・差異分析（製造原価サイクル）
-- 例: mysql -u USER -p eams_db < backend/database/migrations/244_standard_costing_tables.sql
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- 原価標準バージョン（年度・改訂単位）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `cost_standard_versions` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `code` varchar(50) NOT NULL COMMENT '表示コード（例 FY2026-A）',
  `fiscal_year` int NOT NULL COMMENT '会計年度',
  `status` varchar(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/active/archived',
  `effective_from` date NOT NULL COMMENT '適用開始日',
  `effective_to` date DEFAULT NULL COMMENT '適用終了日（NULL=無期限）',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_csv_code` (`code`),
  KEY `idx_csv_year_status` (`fiscal_year`, `status`),
  KEY `idx_csv_effective` (`effective_from`, `effective_to`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価バージョン';


-- ---------------------------------------------------------------------------
-- 製品別標準原価ヘッダ（単位当たり）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `product_standard_costs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `version_id` int NOT NULL COMMENT 'cost_standard_versions.id',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '品番',
  `product_name` varchar(200) DEFAULT NULL COMMENT '品名（スナップショット）',
  `material_cost_std` decimal(18,4) NOT NULL DEFAULT 0.0000 COMMENT '直接材料標準（単位）',
  `labor_cost_std` decimal(18,4) NOT NULL DEFAULT 0.0000 COMMENT '直接労務標準（単位）',
  `overhead_cost_std` decimal(18,4) NOT NULL DEFAULT 0.0000 COMMENT '製造間接標準（単位）',
  `total_cost_std` decimal(18,4) NOT NULL DEFAULT 0.0000 COMMENT '標準原価合計（単位）',
  `currency` varchar(10) NOT NULL DEFAULT 'JPY',
  `source` varchar(30) NOT NULL DEFAULT 'manual' COMMENT 'manual/import/rollup',
  `remarks` text,
  `created_by` varchar(100) DEFAULT NULL,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_psc_ver_prod` (`version_id`, `product_cd`),
  KEY `idx_psc_product` (`product_cd`),
  CONSTRAINT `fk_psc_version` FOREIGN KEY (`version_id`) REFERENCES `cost_standard_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='製品標準原価ヘッダ';


CREATE TABLE IF NOT EXISTS `product_standard_material_lines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `header_id` bigint NOT NULL COMMENT 'product_standard_costs.id',
  `line_no` int NOT NULL DEFAULT 1,
  `material_cd` varchar(50) DEFAULT NULL,
  `material_name` varchar(200) DEFAULT NULL,
  `qty_per_unit` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '単位製品当たり数量',
  `scrap_pct` decimal(9,4) NOT NULL DEFAULT 0 COMMENT 'スクラップ率%',
  `standard_unit_price` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '標準単価',
  `amount` decimal(18,4) NOT NULL DEFAULT 0 COMMENT '金額',
  `bom_line_id` int DEFAULT NULL COMMENT '参照BOM行',
  PRIMARY KEY (`id`),
  KEY `idx_psml_header` (`header_id`),
  CONSTRAINT `fk_psml_header` FOREIGN KEY (`header_id`) REFERENCES `product_standard_costs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価 材料明細';


CREATE TABLE IF NOT EXISTS `product_standard_labor_lines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `header_id` bigint NOT NULL,
  `line_no` int NOT NULL DEFAULT 1,
  `process_cd` varchar(50) DEFAULT NULL,
  `process_name` varchar(200) DEFAULT NULL,
  `std_hours` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '標準直接作業時間',
  `setup_hours` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '段取時間',
  `labor_rate_per_hour` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '標準賃率/時',
  `cost_center_cd` varchar(50) DEFAULT NULL,
  `amount` decimal(18,4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_psll_header` (`header_id`),
  CONSTRAINT `fk_psll_header` FOREIGN KEY (`header_id`) REFERENCES `product_standard_costs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価 労務明細';


CREATE TABLE IF NOT EXISTS `product_standard_overhead_lines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `header_id` bigint NOT NULL,
  `line_no` int NOT NULL DEFAULT 1,
  `cost_center_cd` varchar(50) DEFAULT NULL,
  `allocation_basis` varchar(40) NOT NULL DEFAULT 'machine_hours' COMMENT 'machine_hours/labor_hours/direct_labor_cost',
  `basis_qty_per_unit` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '配賦基準数量/単位',
  `overhead_rate` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '間接費率',
  `amount` decimal(18,4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_psol_header` (`header_id`),
  CONSTRAINT `fk_psol_header` FOREIGN KEY (`header_id`) REFERENCES `product_standard_costs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価 間接費明細';


-- ---------------------------------------------------------------------------
-- 会計期間（月次締め単位）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `cost_accounting_periods` (
  `id` int NOT NULL AUTO_INCREMENT,
  `year_month` char(7) NOT NULL COMMENT 'YYYY-MM',
  `status` varchar(20) NOT NULL DEFAULT 'open' COMMENT 'open/closed',
  `notes` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cap_ym` (`year_month`),
  KEY `idx_cap_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='原価会計期間（月次）';


CREATE TABLE IF NOT EXISTS `cost_period_product_costs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `period_id` int NOT NULL,
  `version_id` int DEFAULT NULL COMMENT '標準計算に用いたバージョン（NULL=自動選択）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_name` varchar(200) DEFAULT NULL,
  `finished_good_qty` decimal(18,4) NOT NULL DEFAULT 0 COMMENT '完成品数量',
  `wip_equivalent_qty` decimal(18,4) NOT NULL DEFAULT 0 COMMENT '仕掛約当数量',
  `actual_material_cost` decimal(18,2) DEFAULT NULL COMMENT '実際材料費（当期）',
  `actual_labor_cost` decimal(18,2) DEFAULT NULL COMMENT '実際労務費',
  `actual_overhead_cost` decimal(18,2) DEFAULT NULL COMMENT '実際間接費',
  `standard_material_allowed` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '標準許容 材料',
  `standard_labor_allowed` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '標準許容 労務',
  `standard_overhead_allowed` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '標準許容 間接',
  `variance_material_price` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '材料価格差異',
  `variance_material_qty` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '材料数量差異',
  `variance_labor_rate` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '賃率差異',
  `variance_labor_efficiency` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '作業時間差異',
  `variance_moh_budget` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '間接予算差異',
  `variance_moh_capacity` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '操業度差異',
  `variance_moh_efficiency` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '間接能率差異',
  `remarks` text,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cpp_period_prod` (`period_id`, `product_cd`),
  KEY `idx_cpp_product` (`product_cd`),
  KEY `idx_cpp_version` (`version_id`),
  CONSTRAINT `fk_cpp_period` FOREIGN KEY (`period_id`) REFERENCES `cost_accounting_periods` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cpp_version` FOREIGN KEY (`version_id`) REFERENCES `cost_standard_versions` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='月次品目別 実績・標準許容・差異';
