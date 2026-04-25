SET NAMES utf8mb4;

CREATE TABLE `error_logs`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日時',
  `level` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'レベル（ERROR/WARN/INFO）',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ソース（サービス名・ファイル名）',
  `message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'エラーメッセージ',
  `stack_trace` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'スタックトレース',
  `user_id` int NULL DEFAULT NULL COMMENT 'ユーザーID',
  `request_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'リクエストID',
  `extra_data` json NULL COMMENT '追加データ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_error_logs_timestamp`(`timestamp` ASC) USING BTREE,
  INDEX `idx_error_logs_level`(`level` ASC) USING BTREE,
  INDEX `idx_error_logs_source`(`source`(100) ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'エラーログテーブル' ROW_FORMAT = Dynamic;
