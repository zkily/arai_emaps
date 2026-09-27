-- 生産注意事項：注意事項 / 品質事項 を同一行の2フィールドに
SET NAMES utf8mb4;

-- quality_text 追加（既にあればスキップ想定でスクリプト側で制御）
ALTER TABLE `quality_product_process_cautions`
  ADD COLUMN `quality_text` VARCHAR(500) NULL COMMENT '品質事項（App表示）'
  AFTER `caution_text`;

-- caution_text を空許可（品質のみ登録できるように）
ALTER TABLE `quality_product_process_cautions`
  MODIFY COLUMN `caution_text` VARCHAR(500) NULL COMMENT '注意事項（App表示）';

-- 既存 matter_kind=quality を quality_text へ退避（同工程・同製品の注意行へマージ）
UPDATE `quality_product_process_cautions` c
INNER JOIN `quality_product_process_cautions` q
  ON q.matter_kind = 'quality'
 AND q.process_code = c.process_code
 AND q.id <> c.id
 AND (
   (c.product_cd IS NULL AND q.product_cd IS NULL)
   OR (c.product_cd IS NOT NULL AND c.product_cd = q.product_cd)
 )
SET c.quality_text = CASE
  WHEN c.quality_text IS NULL OR TRIM(c.quality_text) = '' THEN q.caution_text
  WHEN q.caution_text IS NULL OR TRIM(q.caution_text) = '' THEN c.quality_text
  ELSE CONCAT(c.quality_text, '\n', q.caution_text)
END
WHERE (c.matter_kind IS NULL OR c.matter_kind = '' OR c.matter_kind = 'caution');

-- マージ済みの quality 行を削除
DELETE q FROM `quality_product_process_cautions` q
INNER JOIN `quality_product_process_cautions` c
  ON c.process_code = q.process_code
 AND c.id <> q.id
 AND (c.matter_kind IS NULL OR c.matter_kind = '' OR c.matter_kind = 'caution')
 AND (
   (c.product_cd IS NULL AND q.product_cd IS NULL)
   OR (c.product_cd IS NOT NULL AND c.product_cd = q.product_cd)
 )
WHERE q.matter_kind = 'quality';

-- 残った quality のみ行：内容を quality_text へ移す
UPDATE `quality_product_process_cautions`
SET quality_text = caution_text,
    caution_text = NULL
WHERE matter_kind = 'quality'
  AND (quality_text IS NULL OR TRIM(quality_text) = '');
