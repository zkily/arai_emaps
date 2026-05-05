SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for workflow_definitions
-- ----------------------------
DROP TABLE IF EXISTS `workflow_definitions`;
CREATE TABLE `workflow_definitions`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ワークフローコード（例: WF_PO）',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ワークフロー名',
  `document_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '対象伝票タイプ',
  `approval_route_id` int NULL DEFAULT NULL COMMENT 'デフォルト承認ルートID',
  `timeout_days` int NULL DEFAULT 3 COMMENT '承認期限（日数）',
  `escalation_enabled` tinyint(1) NULL DEFAULT 0 COMMENT 'エスカレーション有効',
  `escalation_days` int NULL DEFAULT NULL COMMENT 'エスカレーションまでの日数',
  `escalation_target` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'エスカレーション先',
  `auto_approve_enabled` tinyint(1) NULL DEFAULT 0 COMMENT '自動承認有効',
  `auto_approve_condition` json NULL COMMENT '自動承認条件',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code` ASC) USING BTREE,
  INDEX `idx_workflow_defs_code`(`code` ASC) USING BTREE,
  INDEX `idx_workflow_defs_doctype`(`document_type` ASC) USING BTREE,
  INDEX `fk_workflow_defs_route`(`approval_route_id` ASC) USING BTREE,
  CONSTRAINT `fk_workflow_defs_route` FOREIGN KEY (`approval_route_id`) REFERENCES `approval_routes` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'ワークフロー定義テーブル' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of workflow_definitions
-- ----------------------------
INSERT INTO `workflow_definitions` VALUES (1, 'WF_PO', '購買発注承認', '発注書', NULL, 3, 1, NULL, NULL, 0, NULL, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `workflow_definitions` VALUES (2, 'WF_SO', '受注承認', '受注書', NULL, 2, 1, NULL, NULL, 0, NULL, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `workflow_definitions` VALUES (3, 'WF_QT', '見積承認', '見積書', NULL, 1, 0, NULL, NULL, 0, NULL, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `workflow_definitions` VALUES (4, 'WF_INV', '請求書承認', '請求書', NULL, 5, 1, NULL, NULL, 0, NULL, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
