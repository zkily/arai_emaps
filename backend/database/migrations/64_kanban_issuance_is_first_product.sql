-- カンバン発行：初回生産マーク（切断現品票の製品名前に「初」表示）
SET NAMES utf8mb4;

ALTER TABLE `kanban_issuance`
  ADD COLUMN `is_first_product` tinyint(1) NULL DEFAULT 0 COMMENT '初（初回生産マーク）' AFTER `has_chamfering_process`;
