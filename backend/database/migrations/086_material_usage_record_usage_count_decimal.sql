-- material_usage_record: usage_count を小数対応（按分時 0.5 等）
SET NAMES utf8mb4;

ALTER TABLE `material_usage_record`
  MODIFY COLUMN `usage_count` decimal(10,4) NOT NULL DEFAULT 1.0000
    COMMENT '使用数（行の usage_count をそのまま、按分時は <1）';
