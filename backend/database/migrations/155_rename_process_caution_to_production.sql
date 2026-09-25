-- 表示名変更：加工注意事項 → 生産注意事項
SET NAMES utf8mb4;

UPDATE menus
SET name = '生産注意事項'
WHERE code = 'ERP_QUALITY_PRODUCT_PROCESS_CAUTION';

ALTER TABLE `quality_product_process_cautions`
  COMMENT = '製品生産注意事項（工程別）';
