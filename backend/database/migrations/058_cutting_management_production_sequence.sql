-- 切断指示：display_order を 生産順（production_sequence）にリネーム
SET NAMES utf8mb4;

-- 既に 057 で display_order が存在する場合のみ実行（057 を未適用の場合は 057 で production_sequence が追加済みのため 058 は不要）
ALTER TABLE `cutting_management`
  DROP INDEX `idx_display_order`;
ALTER TABLE `cutting_management`
  CHANGE COLUMN `display_order` `production_sequence` int NULL DEFAULT 0 COMMENT '生産順（同一切断機内の自動並び順、拖拽可変更）';

ALTER TABLE `cutting_management`
  ADD INDEX `idx_production_sequence` (`production_sequence`);
