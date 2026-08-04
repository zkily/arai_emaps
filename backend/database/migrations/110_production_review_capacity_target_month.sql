-- 生産検討会 工程能力：月別設定（target_month）
-- target_month='' はデフォルト（従来の全社共通マスタ）
SET NAMES utf8mb4;

ALTER TABLE `production_review_capacity`
  ADD COLUMN `target_month` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    NOT NULL DEFAULT '' COMMENT '対象月 YYYY-MM（空=デフォルト）' AFTER `id`;

-- 既存行はデフォルトとして維持
UPDATE `production_review_capacity` SET `target_month` = '' WHERE `target_month` IS NULL OR `target_month` = '';

ALTER TABLE `production_review_capacity`
  DROP INDEX `uk_prc_process_cd`,
  ADD UNIQUE KEY `uk_prc_month_process` (`target_month`, `process_cd`),
  ADD KEY `idx_prc_target_month` (`target_month`);
