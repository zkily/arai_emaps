SET NAMES utf8mb4;

CREATE TABLE `notification_settings`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `event_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'イベントコード',
  `event_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'イベント名',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '説明',
  `in_app_enabled` tinyint(1) NULL DEFAULT 1 COMMENT 'アプリ内通知有効',
  `email_enabled` tinyint(1) NULL DEFAULT 0 COMMENT 'メール通知有効',
  `slack_enabled` tinyint(1) NULL DEFAULT 0 COMMENT 'Slack通知有効',
  `line_enabled` tinyint(1) NULL DEFAULT 0 COMMENT 'LINE通知有効',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `event_code`(`event_code` ASC) USING BTREE,
  INDEX `idx_notification_settings_event`(`event_code` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '通知設定テーブル' ROW_FORMAT = Dynamic;
INSERT INTO `notification_settings` VALUES (1, 'APPROVAL_REQUEST', '承認依頼', '新しい承認依頼が届いた時', 1, 1, 1, 0, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `notification_settings` VALUES (2, 'APPROVAL_COMPLETE', '承認完了', '承認が完了した時', 1, 1, 0, 0, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `notification_settings` VALUES (3, 'APPROVAL_REJECT', '承認却下', '承認が却下された時', 1, 1, 1, 0, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `notification_settings` VALUES (4, 'DELIVERY_ALERT', '納期アラート', '納期が近づいている時', 1, 1, 1, 1, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `notification_settings` VALUES (5, 'STOCK_ALERT', '在庫アラート', '在庫が基準値を下回った時', 1, 1, 1, 0, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `notification_settings` VALUES (6, 'SYSTEM_ERROR', 'システムエラー', 'システムエラーが発生した時', 1, 1, 1, 0, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
