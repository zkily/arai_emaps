-- 既存の parts テーブルに決済種類を追加（215 を「settlement_type 追加前」の内容で既に適用済みの DB 向け）
-- 新規環境で 215（settlement_type 入り）を適用済みの場合は実行しないでください（重複カラムエラーになります）。
SET NAMES utf8mb4;

ALTER TABLE `parts`
  ADD COLUMN `settlement_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '有償支給' COMMENT '決済種類' AFTER `kind`,
  ADD KEY `idx_parts_settlement_type` (`settlement_type`),
  ADD CONSTRAINT `chk_parts_settlement_type` CHECK (`settlement_type` IN ('有償支給','無償支給','自給','その他'));
