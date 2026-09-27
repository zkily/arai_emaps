-- 生産注意事項：区分（注意事項 / 品質事項）
SET NAMES utf8mb4;

ALTER TABLE `quality_product_process_cautions`
  ADD COLUMN `matter_kind` VARCHAR(20) NOT NULL DEFAULT 'caution'
    COMMENT 'caution=注意事項 quality=品質事項'
    AFTER `caution_text`;
