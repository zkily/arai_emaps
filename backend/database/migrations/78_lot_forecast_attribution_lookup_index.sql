-- lot_forecast_attribution：スケジューリングボード管理コード lookup 用
SET NAMES utf8mb4;

ALTER TABLE `lot_forecast_attribution`
  ADD INDEX `idx_lfa_mgmt_current_process` (`management_code`, `is_current`, `process_key`);
