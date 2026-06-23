-- 切断工程実績レポート: 既定対象期間=今月、既定形式=PDF
UPDATE report_definitions
SET
  default_format = 'pdf',
  parameter_schema = '{"fields":[{"key":"date_range","label":"対象期間","type":"date_range","default":"this_month","presets":["yesterday","today","last_week","this_week","last_month","this_month","custom"]}]}'
WHERE report_code = 'CUTTING_DAILY_ACTUAL';
