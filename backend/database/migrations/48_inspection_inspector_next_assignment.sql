-- 検査員別「次製品」指定（検査モニタ → 検査実績収集表示）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inspection_inspector_next_assignment` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `production_day` date NOT NULL COMMENT '生産日',
  `inspector_user_id` int NOT NULL COMMENT '検査員 users.id',
  `next_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '次製品CD',
  `next_product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '次製品名',
  `assigned_by_user_id` int NULL DEFAULT NULL COMMENT '指定者 users.id',
  `assigned_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '指定日時',
  `note` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '備考',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_day_inspector` (`production_day`, `inspector_user_id`),
  INDEX `idx_production_day` (`production_day`),
  INDEX `idx_inspector_user_id` (`inspector_user_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '検査員次製品指定' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
