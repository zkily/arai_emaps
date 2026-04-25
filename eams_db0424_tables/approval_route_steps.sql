SET NAMES utf8mb4;

CREATE TABLE `approval_route_steps`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `route_id` int NOT NULL COMMENT '承認ルートID',
  `step_order` int NOT NULL COMMENT 'ステップ順序（1から開始）',
  `step_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ステップ名（例: 課長）',
  `approver_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '承認者タイプ（role:ロール, user:特定ユーザー, position:役職）',
  `approver_id` int NULL DEFAULT NULL COMMENT '承認者ID（ユーザーID or ロールID）',
  `approver_position` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '役職名',
  `is_optional` tinyint(1) NULL DEFAULT 0 COMMENT 'スキップ可能フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_route_steps_route`(`route_id` ASC) USING BTREE,
  INDEX `idx_route_steps_order`(`route_id` ASC, `step_order` ASC) USING BTREE,
  CONSTRAINT `fk_route_steps_route` FOREIGN KEY (`route_id`) REFERENCES `approval_routes` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '承認ルートステップテーブル' ROW_FORMAT = Dynamic;
INSERT INTO `approval_route_steps` VALUES (1, 1, 1, '申請者', 'position', NULL, '申請者', 0, '2026-02-05 18:08:14');
INSERT INTO `approval_route_steps` VALUES (2, 1, 2, '課長', 'position', NULL, '課長', 0, '2026-02-05 18:08:14');
INSERT INTO `approval_route_steps` VALUES (3, 1, 3, '部長', 'position', NULL, '部長', 0, '2026-02-05 18:08:14');
