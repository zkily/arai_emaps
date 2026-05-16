-- MES 切断実績収集：一時停止累計秒数
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `mes_paused_accum_sec` INT NULL DEFAULT NULL
    COMMENT 'MES一時停止累計秒数(一時停止〜再開の合計)' AFTER `mes_net_production_sec`;
