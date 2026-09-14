-- lot_forecast_attribution の無効版（is_current=0）を退避するアーカイブ表。
-- ホットテーブルは is_current=1 のみ残す。業務照会は従来どおり is_current=1 を参照する。

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `lot_forecast_attribution_archive` LIKE `lot_forecast_attribution`;

ALTER TABLE `lot_forecast_attribution_archive`
  COMMENT = '日内示帰属の無効版退避（lot_forecast_attribution の is_current=0 から移動）';
