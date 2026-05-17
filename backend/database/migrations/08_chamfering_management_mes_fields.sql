-- MES 面取実績収集（cutting_management の 03〜07 と同等）
SET NAMES utf8mb4;

ALTER TABLE `chamfering_management`
  ADD COLUMN `mes_production_started_at` DATETIME NULL DEFAULT NULL
    COMMENT 'MES面取実績収集・生産開始日時' AFTER `remarks`,
  ADD COLUMN `mes_production_ended_at` DATETIME NULL DEFAULT NULL
    COMMENT 'MES面取実績収集・生産終了日時' AFTER `mes_production_started_at`,
  ADD COLUMN `mes_net_production_sec` INT NULL DEFAULT NULL
    COMMENT 'MES净生産秒数(一時停止除く,段取除く)' AFTER `mes_production_ended_at`,
  ADD COLUMN `mes_paused_accum_sec` INT NULL DEFAULT NULL
    COMMENT 'MES一時停止累計秒数' AFTER `mes_net_production_sec`,
  ADD COLUMN `mes_production_is_paused` TINYINT(1) NULL DEFAULT NULL
    COMMENT 'MES稼働計測:1=一時停止中,0=稼働中,NULL=未開始/終了済' AFTER `mes_paused_accum_sec`,
  ADD COLUMN `mes_setup_time_min` INT NULL DEFAULT NULL
    COMMENT 'MES段取時間(分)' AFTER `mes_production_is_paused`,
  ADD COLUMN `mes_operator_user_id` INT NULL DEFAULT NULL
    COMMENT 'MES作業者(users.id)' AFTER `mes_setup_time_min`,
  ADD COLUMN `mes_scanned_code` VARCHAR(512) NULL DEFAULT NULL
    COMMENT 'MES面取実績・バーコード/QR読取' AFTER `mes_operator_user_id`;
