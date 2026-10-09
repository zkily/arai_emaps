-- TABLE: production_plan_excel_juban_recalc_hint
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_plan_excel_juban_recalc_hint` (
  `日付` date NOT NULL,
  `加工機` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_ja_0900_as_cs NOT NULL,
  `queued_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`日付`,`加工機`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_ja_0900_as_cs COMMENT='production_plan_excel 順番重算队列';

SET FOREIGN_KEY_CHECKS = 1;
