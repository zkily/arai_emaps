SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for import_export_history
-- ----------------------------
DROP TABLE IF EXISTS `import_export_history`;
CREATE TABLE `import_export_history`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '種類（import/export）',
  `master_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'マスター種類',
  `filename` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ファイル名',
  `file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ファイルパス',
  `format` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'フォーマット（csv/xlsx）',
  `encoding` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '文字コード',
  `total_records` int NULL DEFAULT 0 COMMENT '総件数',
  `success_records` int NULL DEFAULT 0 COMMENT '成功件数',
  `error_records` int NULL DEFAULT 0 COMMENT 'エラー件数',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'processing' COMMENT 'ステータス（processing/success/partial_error/failed）',
  `error_details` json NULL COMMENT 'エラー詳細',
  `options` json NULL COMMENT 'オプション（update_existing等）',
  `user_id` int NULL DEFAULT NULL COMMENT '実行ユーザーID',
  `started_at` datetime NULL DEFAULT NULL COMMENT '開始日時',
  `completed_at` datetime NULL DEFAULT NULL COMMENT '完了日時',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_import_export_type`(`type` ASC) USING BTREE,
  INDEX `idx_import_export_master`(`master_type` ASC) USING BTREE,
  INDEX `idx_import_export_status`(`status` ASC) USING BTREE,
  INDEX `idx_import_export_user`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'インポート/エクスポート履歴テーブル' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of import_export_history
-- ----------------------------

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
