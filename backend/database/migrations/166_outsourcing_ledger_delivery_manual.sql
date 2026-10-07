-- 外注メッキ／外注溶接 日別台帳：納期の手修正フラグ（マスタ反映で納期を上書きしない）
SET NAMES utf8mb4;

ALTER TABLE `outsourcing_plating_ledger`
  ADD COLUMN `delivery_date_manual` tinyint(1) NOT NULL DEFAULT 0 COMMENT '納期手修正' AFTER `delivery_date`;

ALTER TABLE `outsourcing_welding_ledger`
  ADD COLUMN `delivery_date_manual` tinyint(1) NOT NULL DEFAULT 0 COMMENT '納期手修正' AFTER `delivery_date`;
