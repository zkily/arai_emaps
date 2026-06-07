-- backend/database/migrations/11_cutting_management_mes_blade_repair_min.sql
ALTER TABLE `cutting_management`
  ADD COLUMN `mes_saw_blade_exchange_min` INT NULL DEFAULT NULL
    COMMENT 'MES鋸刃交換時間(分)' AFTER `mes_setup_time_min`,
  ADD COLUMN `mes_repair_min` INT NULL DEFAULT NULL
    COMMENT 'MES修理時間(分)' AFTER `mes_saw_blade_exchange_min`;