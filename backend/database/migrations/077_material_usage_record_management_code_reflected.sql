-- ============================================================
-- Migration 077: material_usage_record に管理コード・反映済を追加
-- ============================================================

SET NAMES utf8mb4;

ALTER TABLE `material_usage_record`
  ADD COLUMN `management_codes` text COMMENT '管理コード（複数はカンマ区切り）' AFTER `source`,
  ADD COLUMN `reflected` tinyint(1) NOT NULL DEFAULT 0 COMMENT '反映済（0=未反映, 1=反映済）' AFTER `management_codes`;
