-- SEED: report_definitions
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `report_definitions` (`id`, `report_code`, `report_name`, `category`, `default_format`, `parameter_schema`, `event_code`, `description`, `is_active`) VALUES
(1, 'CUTTING_DAILY_ACTUAL', '切断工程実績レポート', 'MES', 'pdf', '{\"fields\": [{\"key\": \"date_range\", \"type\": \"date_range\", \"label\": \"対象期間\", \"default\": \"this_month\", \"presets\": [\"yesterday\", \"today\", \"last_week\", \"this_week\", \"last_month\", \"this_month\", \"custom\"]}]}', 'REPORT_CUTTING_DAILY_ACTUAL', '切断実績（設備別件数・数量・明細）を集計し添付配信', 1),
(2, 'INVENTORY_TREND_WEEKLY', '在庫推移レポート', 'ERP', 'xlsx', '{\"fields\": [{\"key\": \"date_range\", \"type\": \"date_range\", \"label\": \"対象期間\", \"default\": \"last_week\", \"presets\": [\"last_week\", \"this_week\", \"last_month\", \"this_month\", \"custom\"]}]}', 'REPORT_INVENTORY_TREND_WEEKLY', '工程別の在庫推移を集計し添付配信', 1),
(3, 'PLAN_ACTUAL_MONTHLY', '計画実績対比レポート', 'APS', 'xlsx', '{\"fields\": [{\"key\": \"month\", \"type\": \"month\", \"label\": \"基準月\", \"default\": \"last_month\"}]}', 'REPORT_PLAN_ACTUAL_MONTHLY', '計画（ベースライン）と実績の月次対比を集計し添付配信', 1),
(4, 'PLAN_BASELINE_WEEKLY', '生産計画ベースラインレポート', 'APS', 'pdf', '{\"fields\": [{\"key\": \"month\", \"type\": \"month\", \"label\": \"基準月\", \"default\": \"this_month\"}]}', 'REPORT_PLAN_BASELINE_WEEKLY', '基準計画と実績の工程別比較をPDF添付で週次配信', 1);

SET FOREIGN_KEY_CHECKS = 1;
