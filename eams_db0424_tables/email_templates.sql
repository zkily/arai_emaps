SET NAMES utf8mb4;

CREATE TABLE `email_templates`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'テンプレートコード',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'テンプレート名',
  `subject` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '件名（変数可）',
  `body` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '本文（HTML可、変数可）',
  `event_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '関連イベントコード',
  `language` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'ja' COMMENT '言語',
  `variables` json NULL COMMENT '利用可能な変数一覧',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code` ASC) USING BTREE,
  INDEX `idx_email_templates_code`(`code` ASC) USING BTREE,
  INDEX `idx_email_templates_event`(`event_code` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'メールテンプレートテーブル' ROW_FORMAT = Dynamic;
INSERT INTO `email_templates` VALUES (1, 'APPROVAL_REQUEST', '承認依頼', '【要承認】{document_type} #{document_no}', '<p>{approver_name}様</p><p>以下の承認依頼が届いています。</p><p>伝票種類: {document_type}<br>伝票番号: {document_no}<br>申請者: {requester_name}<br>金額: {amount}</p><p>システムにログインして承認処理を行ってください。</p>', 'APPROVAL_REQUEST', 'ja', NULL, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `email_templates` VALUES (2, 'APPROVAL_COMPLETE', '承認完了', '【承認完了】{document_type} #{document_no}', '<p>{requester_name}様</p><p>以下の申請が承認されました。</p><p>伝票種類: {document_type}<br>伝票番号: {document_no}<br>承認者: {approver_name}</p>', 'APPROVAL_COMPLETE', 'ja', NULL, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `email_templates` VALUES (3, 'PASSWORD_RESET', 'パスワードリセット', '【Smart-EMAP】パスワードリセット', '<p>{user_name}様</p><p>パスワードがリセットされました。</p><p>新しいパスワードでログインしてください。</p>', NULL, 'ja', NULL, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `email_templates` VALUES (4, 'WELCOME', 'ようこそ', '【Smart-EMAP】アカウント作成完了', '<p>{user_name}様</p><p>Smart-EMAPへようこそ！</p><p>アカウントが作成されました。以下の情報でログインしてください。</p><p>ユーザー名: {username}<br>初期パスワード: {initial_password}</p>', NULL, 'ja', NULL, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
