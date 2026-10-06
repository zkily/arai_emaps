-- 外注メッキ日別台帳：受入・不良の管理番号（注文番号とは独立。在庫取引記録の order_no に使う）
SET NAMES utf8mb4;

ALTER TABLE `outsourcing_plating_ledger`
  ADD COLUMN `receiving_no` varchar(30) NULL COMMENT '受入管理番号' AFTER `receiving_qty`,
  ADD COLUMN `disposal_no` varchar(30) NULL COMMENT '不良管理番号' AFTER `defect_qty`,
  ADD UNIQUE KEY `uk_plating_ledger_receiving_no` (`receiving_no`),
  ADD UNIQUE KEY `uk_plating_ledger_disposal_no` (`disposal_no`);
