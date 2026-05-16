-- MES 切断実績収集：生産開始/終了時刻・段取（分）・作業者(users.id)
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `mes_production_started_at` DATETIME NULL DEFAULT NULL
    COMMENT 'MES切断実績収集・生産開始日時' AFTER `usage_count`,
  ADD COLUMN `mes_production_ended_at` DATETIME NULL DEFAULT NULL
    COMMENT 'MES切断実績収集・生産終了日時' AFTER `mes_production_started_at`,
  ADD COLUMN `mes_setup_time_min` INT NULL DEFAULT NULL
    COMMENT 'MES段取時間(分)' AFTER `mes_production_ended_at`,
  ADD COLUMN `mes_operator_user_id` INT NULL DEFAULT NULL
    COMMENT 'MES作業者(users.id)' AFTER `mes_setup_time_min`;
