-- 041: outsourcing_welding_orders に notes 列を追加
-- 理由: 本テーブルに対する UPDATE 時に発火するトリガーが 'notes' を参照しており、
--       テーブル定義に notes が無いため 1054 Unknown column 'notes' が発生する。
--       列を追加してトリガーとの互換を取る（アプリは remarks のみ使用）。
-- 実行後、不要なトリガーは SHOW TRIGGERS WHERE `Table` = 'outsourcing_welding_orders'; で確認し削除可能。

ALTER TABLE `outsourcing_welding_orders`
  ADD COLUMN `notes` TEXT NULL COMMENT '備考(trigger互換)' AFTER `remarks`;
