-- ============================================================
-- Migration 075: 材料使用済テーブル作成
-- 切断工程の材料使用数を日次で管理し、
-- material_stock.planned_usage の更新ソースとして使用する。
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `material_usage_record` (
  `id`            int           NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `usage_date`    date          NOT NULL                COMMENT '使用日（生産日）',
  `material_cd`   varchar(50)   NOT NULL                COMMENT '材料CD（materials テーブル参照）',
  `material_name` varchar(255)  NOT NULL                COMMENT '材料名（冗長保持）',
  `usage_count`   int           NOT NULL DEFAULT 0      COMMENT '使用数（その日・その材料の不重複管理コード数）',
  `source`        varchar(50)   NOT NULL DEFAULT 'cutting' COMMENT '来源区分（cutting / chamfering など）',
  `created_at`    timestamp     NULL DEFAULT CURRENT_TIMESTAMP   COMMENT '作成日時',
  `updated_at`    timestamp     NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_usage_date_material_cd_source` (`usage_date`, `material_cd`, `source`)
    COMMENT '同一日・同一材料・同一ソースは1行（UPSERT対応）',
  KEY `idx_usage_date`  (`usage_date`),
  KEY `idx_material_cd` (`material_cd`),
  KEY `idx_source`      (`source`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '材料使用済テーブル（切断工程等の日次材料使用数を管理）';

SET FOREIGN_KEY_CHECKS = 1;
