-- MES 切断実績：鋸刃交換（分）・修理（分）
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `mes_saw_blade_exchange_min` INT NULL DEFAULT NULL
    COMMENT 'MES鋸刃交換時間(分)' AFTER `mes_setup_time_min`,
  ADD COLUMN `mes_repair_min` INT NULL DEFAULT NULL
    COMMENT 'MES修理時間(分)' AFTER `mes_saw_blade_exchange_min`;
