-- ============================================================
-- Migration 074: 材料管理テーブル作成
-- 対象: material_inspection_master / material_logs /
--       material_stock / material_stock_sub / stock_materials
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------
-- 1. 材料検品基準マスタ (material_inspection_master)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `material_inspection_master` (
  `id`                  int          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `inspection_cd`       varchar(50)  NOT NULL COMMENT '検験代码',
  `inspection_standard` text         NOT NULL COMMENT '検験基準',
  `created_at`          timestamp    NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at`          timestamp    NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_inspection_cd` (`inspection_cd`) COMMENT '検験代码一意'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '材料検品基準マスタ';

-- ------------------------------------------------------------
-- 2. 材料受入ログ (material_logs)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `material_logs` (
  `id`               bigint         NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `item`             varchar(100)   NOT NULL COMMENT '項目',
  `material_cd`      varchar(50)    NOT NULL COMMENT '製品CD',
  `material_name`    varchar(255)   NULL DEFAULT NULL COMMENT '製品名',
  `process_cd`       varchar(50)    NOT NULL COMMENT '工程CD',
  `log_date`         date           NOT NULL COMMENT '日付',
  `log_time`         time           NOT NULL COMMENT '時間',
  `hd_no`            varchar(50)    NULL DEFAULT NULL COMMENT 'HD番号',
  `pieces_per_bundle` int           NULL DEFAULT NULL COMMENT '1束あたりの本数',
  `quantity`         int            NULL DEFAULT NULL COMMENT '数量',
  `bundle_quantity`  int            NULL DEFAULT NULL COMMENT '束数量',
  `manufacture_no`   varchar(100)   NULL DEFAULT NULL COMMENT '製造番号',
  `manufacture_date` date           NULL DEFAULT NULL COMMENT '製造日',
  `length`           int            NULL DEFAULT NULL COMMENT '長さ(mm)',
  `outer_diameter1`  decimal(10,4)  NULL DEFAULT NULL COMMENT '外径1(mm)',
  `outer_diameter2`  decimal(10,4)  NULL DEFAULT NULL COMMENT '外径2(mm)',
  `magnetic`         varchar(1)     NULL DEFAULT NULL COMMENT '磁気',
  `appearance`       varchar(1)     NULL DEFAULT NULL COMMENT '外観',
  `supplier`         varchar(255)   NULL DEFAULT NULL COMMENT '仕入先',
  `material_quality` varchar(100)   NULL DEFAULT NULL COMMENT '材質',
  `remarks`          text           NULL COMMENT '備考',
  `note`             varchar(255)   NULL DEFAULT NULL COMMENT 'メモ',
  `created_at`       timestamp      NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at`       timestamp      NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_material_cd`  (`material_cd`),
  KEY `idx_process_cd`   (`process_cd`),
  KEY `idx_log_date`     (`log_date`),
  KEY `idx_manufacture_no` (`manufacture_no`),
  KEY `idx_supplier`     (`supplier`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '材料受入ログ';

-- ------------------------------------------------------------
-- 3. 材料在庫メイン (material_stock)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `material_stock` (
  `id`                   int           NOT NULL AUTO_INCREMENT,
  `material_cd`          varchar(50)   NOT NULL COMMENT '材料CD',
  `material_name`        varchar(50)   NOT NULL COMMENT '材料名',
  `date`                 date          NOT NULL DEFAULT '2025-01-01' COMMENT '日付',
  `initial_stock`        int           NULL DEFAULT 0  COMMENT '初期在庫',
  `current_stock`        int           NULL DEFAULT 0  COMMENT '現在在庫',
  `safety_stock`         int           NULL DEFAULT 0  COMMENT '安全在庫',
  `planned_usage`        int           NULL DEFAULT 0  COMMENT '使用数',
  `adjustment_quantity`  int           NULL DEFAULT 0  COMMENT '調整数',
  `max_stock`            int           NULL DEFAULT 0  COMMENT '最大在庫',
  `standard_spec`        varchar(50)   NULL DEFAULT '' COMMENT '規格',
  `unit`                 varchar(20)   NULL DEFAULT NULL COMMENT '単位',
  `unit_price`           decimal(15,2) NULL DEFAULT 0.00 COMMENT '単価',
  `pieces_per_bundle`    int           NULL DEFAULT 0  COMMENT '束当たり本数',
  `long_weight`          decimal(15,2) NULL DEFAULT NULL COMMENT '一本重量',
  `supplier_cd`          varchar(15)   NULL DEFAULT NULL COMMENT '仕入先CD',
  `supplier_name`        varchar(50)   NULL DEFAULT NULL COMMENT '仕入先名',
  `lead_time`            int           NULL DEFAULT 0  COMMENT 'リードタイム(日)',
  `bundle_quantity`      int           NULL DEFAULT 0  COMMENT '束本数',
  `bundle_weight`        decimal(15,2) NULL DEFAULT 0.00 COMMENT '束重量(kg)',
  `order_quantity`       int           NULL DEFAULT 0  COMMENT '注文数',
  `order_bundle_quantity` int          NULL DEFAULT 0  COMMENT '注文本数',
  `order_amount`         decimal(15,2) NULL DEFAULT 0.00 COMMENT '注文金額',
  `last_updated`         timestamp     NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最終更新日時',
  `created_at`           timestamp     NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `remarks`              varchar(50)   NULL DEFAULT '' COMMENT '備考',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_material_cd_date` (`material_cd`, `date`),
  KEY `idx_material_cd`   (`material_cd`),
  KEY `idx_supplier_cd`   (`supplier_cd`),
  KEY `idx_current_stock` (`current_stock`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '材料在庫メイン';

-- ------------------------------------------------------------
-- 4. 材料在庫サブ / 手動注文 (material_stock_sub)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `material_stock_sub` (
  `id`                   int           NOT NULL AUTO_INCREMENT,
  `material_cd`          varchar(50)   NOT NULL COMMENT '材料CD',
  `material_name`        varchar(255)  NOT NULL COMMENT '材料名',
  `date`                 date          NOT NULL COMMENT '日期',
  `current_stock`        decimal(10,2) NULL DEFAULT 0.00 COMMENT '現在在庫',
  `safety_stock`         decimal(10,2) NULL DEFAULT 0.00 COMMENT '安全在庫',
  `max_stock`            decimal(10,2) NULL DEFAULT 0.00 COMMENT '最大在庫',
  `unit`                 varchar(20)   NULL DEFAULT NULL COMMENT '単位',
  `unit_price`           decimal(10,2) NULL DEFAULT 0.00 COMMENT '単価',
  `supplier_cd`          varchar(50)   NULL DEFAULT NULL COMMENT '仕入先CD',
  `supplier_name`        varchar(255)  NULL DEFAULT NULL COMMENT '仕入先名',
  `lead_time`            int           NULL DEFAULT 0    COMMENT 'リードタイム',
  `planned_usage`        decimal(10,2) NULL DEFAULT 0.00 COMMENT '計画使用数',
  `order_quantity`       decimal(10,2) NULL DEFAULT 0.00 COMMENT '注文束数',
  `order_bundle_quantity` decimal(10,2) NULL DEFAULT 0.00 COMMENT '注文本数',
  `bundle_weight`        decimal(10,2) NULL DEFAULT 0.00 COMMENT '捆重量',
  `order_amount`         decimal(15,2) NULL DEFAULT 0.00 COMMENT '注文金額',
  `standard_spec`        varchar(255)  NULL DEFAULT NULL COMMENT '規格',
  `pieces_per_bundle`    int           NULL DEFAULT 0    COMMENT '每捆件数',
  `long_weight`          decimal(10,2) NULL DEFAULT 0.00 COMMENT '长重量',
  `remarks`              text          NULL COMMENT '備考',
  `created_at`           timestamp     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `last_updated`         timestamp     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最終更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_material_cd_date` (`material_cd`, `date`),
  KEY `idx_date`         (`date`),
  KEY `idx_supplier_cd`  (`supplier_cd`),
  KEY `idx_created_at`   (`created_at`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '材料在庫サブ（手動注文データ）';

-- ------------------------------------------------------------
-- 5. 在庫材料管理 (stock_materials)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `stock_materials` (
  `id`               int          NOT NULL AUTO_INCREMENT COMMENT '在庫材料ID',
  `material_name`    varchar(255) NOT NULL COMMENT '材料名称',
  `manufacture_no`   varchar(100) NOT NULL COMMENT '制造编号',
  `quantity`         int          NOT NULL DEFAULT 0 COMMENT '库存数量',
  `log_date`         date         NOT NULL COMMENT '日志日期',
  `supplier`         varchar(255) NULL DEFAULT NULL COMMENT '供应商',
  `material_quality` varchar(100) NULL DEFAULT NULL COMMENT '材料质量',
  `is_used`          tinyint(1)   NOT NULL DEFAULT 0 COMMENT '是否已使用(0=未使用,1=已使用)',
  `note`             varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `created_at`       timestamp    NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`       timestamp    NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_material_name`  (`material_name`),
  KEY `idx_manufacture_no` (`manufacture_no`),
  KEY `idx_log_date`       (`log_date`),
  KEY `idx_supplier`       (`supplier`),
  KEY `idx_is_used`        (`is_used`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '在庫材料管理表';

SET FOREIGN_KEY_CHECKS = 1;
