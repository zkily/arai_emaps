-- cutting_management: 使用サブ在庫フラグ・材料使用数（instruction_plans と同様）
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `use_material_stock_sub` tinyint(1) NOT NULL DEFAULT 0
    COMMENT '使用サブ在庫（0=反映対象, 1=対象外・material_stock_subで手動）' AFTER `material_usage_reflected`,
  ADD COLUMN `usage_count` decimal(10,4) NOT NULL DEFAULT 1.0000
    COMMENT '材料使用数（1=1本, <1=他行と同一本を按分）' AFTER `use_material_stock_sub`;
