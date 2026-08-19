-- 成型指示書発行管理：設備名×生産日の手入力備考（APS 排産表は変更しない）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `mes_plan_machine_remarks` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `process_name` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '成型' COMMENT '工程（成型/溶接）',
  `plan_date` date NOT NULL COMMENT '生産日',
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '設備名',
  `remarks` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '手入力備考',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_mes_plan_machine_remarks` (`process_name`, `plan_date`, `machine_name`),
  KEY `idx_mes_plan_machine_remarks_date` (`process_name`, `plan_date`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'MES計画 設備名×生産日 手入力備考' ROW_FORMAT = Dynamic;
