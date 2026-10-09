-- TABLE: destination_workdays
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `destination_workdays` (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先マスタCD',
  `work_date` date NOT NULL COMMENT '土日の出勤日',
  `reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '理由',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `unique_work_day` (`destination_cd`,`work_date`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC COMMENT='納入先臨時出勤日マスタ（休日例外）';

SET FOREIGN_KEY_CHECKS = 1;
