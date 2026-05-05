SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for delegations
-- ----------------------------
DROP TABLE IF EXISTS `delegations`;
CREATE TABLE `delegations`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `delegator_id` int NOT NULL COMMENT '委任者ユーザーID',
  `delegate_id` int NOT NULL COMMENT '代理者ユーザーID',
  `start_date` date NOT NULL COMMENT '開始日',
  `end_date` date NOT NULL COMMENT '終了日',
  `scope` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'all' COMMENT '範囲（all:全承認, specific:特定）',
  `scope_details` json NULL COMMENT '範囲詳細（特定の場合）',
  `reason` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '理由',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT 'ステータス（active/expired/cancelled）',
  `created_by` int NULL DEFAULT NULL COMMENT '作成者',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_delegations_delegator`(`delegator_id` ASC) USING BTREE,
  INDEX `idx_delegations_delegate`(`delegate_id` ASC) USING BTREE,
  INDEX `idx_delegations_dates`(`start_date` ASC, `end_date` ASC) USING BTREE,
  INDEX `idx_delegations_status`(`status` ASC) USING BTREE,
  CONSTRAINT `fk_delegations_delegate` FOREIGN KEY (`delegate_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_delegations_delegator` FOREIGN KEY (`delegator_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '代理承認テーブル' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of delegations
-- ----------------------------

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
