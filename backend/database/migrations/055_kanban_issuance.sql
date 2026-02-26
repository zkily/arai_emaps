-- カンバン発行テーブル（kanban_issuance）：切断・面取等の工程別カンバン発行
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `kanban_issuance`;
CREATE TABLE `kanban_issuance` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `process_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程（cutting=切断 / chamfering=面取）',
  `source_id` int NOT NULL COMMENT '元指示ID（cutting_management.id または chamfering_management.id）',
  `kanban_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'カンバン番号',
  `issue_date` date NULL DEFAULT NULL COMMENT '発行日',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'issued' COMMENT '状態（issued=発行済 / completed=完了）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  INDEX `idx_process_type` (`process_type`),
  INDEX `idx_source_id` (`source_id`),
  INDEX `idx_issue_date` (`issue_date`),
  INDEX `idx_kanban_no` (`kanban_no`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'カンバン発行' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
