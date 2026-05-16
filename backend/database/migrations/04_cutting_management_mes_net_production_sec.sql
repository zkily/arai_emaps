-- MES 切断実績収集：净生产秒数（不含暂停、不含段取）
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `mes_net_production_sec` INT NULL DEFAULT NULL
    COMMENT 'MES净生産秒数(一時停止除く,段取除く)' AFTER `mes_production_ended_at`;
