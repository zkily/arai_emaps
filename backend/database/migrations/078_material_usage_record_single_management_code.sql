-- ============================================================
-- Migration 078: material_usage_record に単一管理コード列追加・ユニークキー変更
-- 旧: UNIQUE KEY (usage_date, material_cd, source)  → 集計単位での重複排除
-- 新: UNIQUE KEY (management_code, source)           → 管理コード単位での重複排除
--     management_code: cutting_management.management_code と1対1で対応（1行1件）
-- ============================================================

SET NAMES utf8mb4;

ALTER TABLE `material_usage_record`
  ADD COLUMN `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
      DEFAULT NULL
      COMMENT '管理コード（単一、cutting_management.management_code に対応）'
      AFTER `management_codes`,
  DROP KEY `uk_usage_date_material_cd_source`,
  ADD UNIQUE KEY `uk_management_code_source` (`management_code`, `source`);
