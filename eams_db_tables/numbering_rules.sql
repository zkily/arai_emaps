SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for numbering_rules
-- ----------------------------
DROP TABLE IF EXISTS `numbering_rules`;
CREATE TABLE `numbering_rules`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ルールコード（例: SALES_ORDER）',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ルール名（例: 受注番号）',
  `prefix` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'プレフィックス（例: SO）',
  `format` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'フォーマット（例: {PREFIX}-{YYYY}{MM}-{SEQ:4}）',
  `start_number` int NOT NULL DEFAULT 1 COMMENT '連番開始値',
  `increment` int NOT NULL DEFAULT 1 COMMENT '連番増分',
  `current_number` int NOT NULL DEFAULT 0 COMMENT '現在の連番',
  `reset_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'monthly' COMMENT 'リセットタイミング（never/daily/monthly/yearly）',
  `last_reset_date` date NULL DEFAULT NULL COMMENT '最終リセット日',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '説明',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code` ASC) USING BTREE,
  INDEX `idx_numbering_rules_code`(`code` ASC) USING BTREE,
  INDEX `idx_numbering_rules_active`(`is_active` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '採番ルールテーブル' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of numbering_rules
-- ----------------------------
INSERT INTO `numbering_rules` VALUES (1, 'SALES_ORDER', '受注番号', 'SO', '{PREFIX}-{YYYY}{MM}-{SEQ:4}', 1, 1, 0, 'monthly', NULL, 1, NULL, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `numbering_rules` VALUES (2, 'QUOTATION', '見積番号', 'QT', '{PREFIX}-{YYYY}{MM}{DD}-{SEQ:3}', 1, 1, 0, 'daily', NULL, 1, NULL, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `numbering_rules` VALUES (3, 'PURCHASE_ORDER', '発注番号', 'PO', '{PREFIX}-{YYYY}-{SEQ:5}', 1, 1, 0, 'yearly', NULL, 1, NULL, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `numbering_rules` VALUES (4, 'INVOICE', '請求書番号', 'INV', '{PREFIX}{YYYY}{MM}-{SEQ:4}', 1, 1, 0, 'monthly', NULL, 1, NULL, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `numbering_rules` VALUES (5, 'SHIPMENT', '出荷番号', 'SHP', '{PREFIX}-{YYYY}{MM}{DD}-{SEQ:3}', 1, 1, 0, 'daily', NULL, 1, NULL, '2026-02-05 18:08:14', '2026-02-05 18:08:14');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
