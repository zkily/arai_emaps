-- 外注メッキ日別台帳：注文書の発行記録（注文数を変更すると未発行に戻る）
SET NAMES utf8mb4;

ALTER TABLE `outsourcing_plating_ledger`
  ADD COLUMN `order_sheet_issued_at` datetime NULL COMMENT '注文書発行日時' AFTER `order_amount`,
  ADD COLUMN `order_sheet_issued_by` varchar(100) NULL COMMENT '注文書発行者' AFTER `order_sheet_issued_at`;
