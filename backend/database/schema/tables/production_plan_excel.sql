-- TABLE: production_plan_excel
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_plan_excel` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `日付` date NOT NULL COMMENT '日付',
  `加工機` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_ja_0900_as_cs NOT NULL COMMENT '加工機',
  `製品CD` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_ja_0900_as_cs NOT NULL COMMENT '製品コード',
  `製品名` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_ja_0900_as_cs NOT NULL COMMENT '製品名',
  `加工計画` int NOT NULL COMMENT '加工計画（予定数量）',
  `生産順番` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_ja_0900_as_cs NOT NULL COMMENT '生産順番 (1または2)',
  `順番` tinyint unsigned DEFAULT NULL COMMENT '順番',
  `検索` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_ja_0900_as_cs GENERATED ALWAYS AS (concat(date_format(`日付`,_utf8mb4'%Y%m%d'),right(`加工機`,2),coalesce(cast(`順番` as char charset utf8mb4),_utf8mb4''))) STORED COMMENT '検索キー (自動生成: 年月日 + 加工機後方2桁 + 順番)',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_plan` (`日付`,`加工機`,`製品CD`,`生産順番`) USING BTREE,
  CONSTRAINT `production_plan_excel_chk_seisan_junban` CHECK (((`生産順番` >= 0) and (`生産順番` <= 99)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_ja_0900_as_cs ROW_FORMAT=DYNAMIC COMMENT='生産計画テーブル';

SET FOREIGN_KEY_CHECKS = 1;
