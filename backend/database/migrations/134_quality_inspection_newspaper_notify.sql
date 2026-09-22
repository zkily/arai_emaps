-- 品質管理：検査新聞紙通知（切断実績確定後の自動メール）
--   対象製品テーブル + 通知イベント INSPECTION_NEWSPAPER_ALERT + メールテンプレート
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `quality_inspection_newspaper_products` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品名（表示・メール用）',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_quality_inspection_newspaper_products_cd` (`product_cd`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '検査新聞紙通知 対象製品' ROW_FORMAT = Dynamic;

INSERT INTO notification_settings (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled, is_active)
VALUES
('INSPECTION_NEWSPAPER_ALERT', '実績工程通知', '切断実績確定時、対象製品があれば検査工程へ新聞紙投入を自動メールで通知', 0, 1, 0, 0, 1)
ON DUPLICATE KEY UPDATE event_name = VALUES(event_name), description = VALUES(description);

INSERT INTO email_templates (code, name, subject, body, event_code, language, variables, is_active)
VALUES
(
  'INSPECTION_NEWSPAPER_ALERT',
  '実績工程通知',
  '【Smart-EMAP】検査工程：新聞紙投入のお願い（{production_day}）',
  '<p>切断実績が確定されました。以下の製品は最終工程（検査）で<strong>新聞紙を入れて</strong>ください。</p><p>生産日: {production_day}<br>対象製品数: {product_count} 品目<br>計画数合計: {total_quantity} 本</p>{product_table}<p>Smart-EMAP 生産管理システム</p>',
  'INSPECTION_NEWSPAPER_ALERT',
  'ja',
  '["production_day","product_table","product_count","total_quantity"]',
  1
)
ON DUPLICATE KEY UPDATE name = VALUES(name), subject = VALUES(subject), body = VALUES(body);

-- 品質管理配下にメニュー追加
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_QUALITY_INSPECTION_NEWSPAPER', '実績工程通知', m.id, '/erp/quality/inspection-newspaper', 'Message', 3
FROM menus m
WHERE m.code = 'ERP_QUALITY'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_QUALITY'
SET cfg.name = '実績工程通知',
    cfg.parent_id = parent.id,
    cfg.path = '/erp/quality/inspection-newspaper',
    cfg.icon = 'Message',
    cfg.sort_order = 3
WHERE cfg.code = 'ERP_QUALITY_INSPECTION_NEWSPAPER';

-- 親メニュー（品質管理）を見られるロールへ権限付与 + 管理者
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'ERP_QUALITY'
INNER JOIN menus child ON child.code = 'ERP_QUALITY_INSPECTION_NEWSPAPER';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_QUALITY_INSPECTION_NEWSPAPER';
