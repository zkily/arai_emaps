-- MES 切断実績収集：03〜06 を一括適用（未実行のものだけ手動で実行してください）
-- 既に列がある場合は該当 ALTER をスキップしてください（Duplicate column エラー）
SET NAMES utf8mb4;

-- 03
ALTER TABLE `cutting_management`
  ADD COLUMN `mes_production_started_at` DATETIME NULL DEFAULT NULL
    COMMENT 'MES切断実績収集・生産開始日時' AFTER `usage_count`,
  ADD COLUMN `mes_production_ended_at` DATETIME NULL DEFAULT NULL
    COMMENT 'MES切断実績収集・生産終了日時' AFTER `mes_production_started_at`,
  ADD COLUMN `mes_setup_time_min` INT NULL DEFAULT NULL
    COMMENT 'MES段取時間(分)' AFTER `mes_production_ended_at`,
  ADD COLUMN `mes_operator_user_id` INT NULL DEFAULT NULL
    COMMENT 'MES作業者(users.id)' AFTER `mes_setup_time_min`;

-- 04
ALTER TABLE `cutting_management`
  ADD COLUMN `mes_net_production_sec` INT NULL DEFAULT NULL
    COMMENT 'MES净生産秒数(一時停止除く,段取除く)' AFTER `mes_production_ended_at`;

-- 05
ALTER TABLE `cutting_management`
  ADD COLUMN `mes_paused_accum_sec` INT NULL DEFAULT NULL
    COMMENT 'MES一時停止累計秒数(一時停止〜再開の合計)' AFTER `mes_net_production_sec`;

-- 06
ALTER TABLE `cutting_management`
  ADD COLUMN `mes_scanned_code` VARCHAR(512) NULL DEFAULT NULL
    COMMENT 'MES切断実績・バーコード/QR読取' AFTER `mes_operator_user_id`;
