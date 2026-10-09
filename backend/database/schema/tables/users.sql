-- TABLE: users
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ユーザーID（主キー）',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ユーザー名（ログインID、一意制約）',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'メールアドレス（一意制約）',
  `hashed_password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ハッシュ化されたパスワード',
  `qr_login_token` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ログインQRトークン（パスワードとは別）',
  `full_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '氏名（フルネーム）',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'user' COMMENT 'ユーザーロール',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT 'アカウント有効フラグ',
  `last_login_token` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '単一デバイスログイン用トークン',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `department_id` int DEFAULT NULL COMMENT '所属部門ID',
  `two_factor_enabled` tinyint(1) DEFAULT '0' COMMENT '二要素認証有効フラグ',
  `last_login_at` timestamp NULL DEFAULT NULL COMMENT '最終ログイン日時',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'active' COMMENT 'ステータス（active/locked/inactive）',
  `section_id` int DEFAULT NULL COMMENT '所属課ID',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `idx_username` (`username`) USING BTREE,
  UNIQUE KEY `idx_email` (`email`) USING BTREE,
  UNIQUE KEY `uk_users_qr_login_token` (`qr_login_token`),
  KEY `idx_users_department` (`department_id`),
  KEY `idx_users_status` (`status`),
  KEY `idx_users_section` (`section_id`),
  CONSTRAINT `fk_users_department` FOREIGN KEY (`department_id`) REFERENCES `organizations` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_users_section` FOREIGN KEY (`section_id`) REFERENCES `organizations` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザーマスターテーブル';

SET FOREIGN_KEY_CHECKS = 1;
