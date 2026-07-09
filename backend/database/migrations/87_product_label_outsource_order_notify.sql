-- 成型用ラベル 外注注文メール通知
SET NAMES utf8mb4;

INSERT INTO notification_settings (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled, is_active)
VALUES
('PRODUCT_LABEL_OUTSOURCE_ORDER', '成型用ラベル 外注注文', '外注区分のラベル注文をメール送信（注文一覧＋現品票PDF添付）', 0, 1, 0, 0, 1)
ON DUPLICATE KEY UPDATE event_name = VALUES(event_name), description = VALUES(description);

INSERT INTO email_templates (code, name, subject, body, event_code, language, variables, is_active)
VALUES
(
  'PRODUCT_LABEL_OUTSOURCE_ORDER',
  '成型用ラベル 外注注文',
  '【Smart-EMAP】外注ラベル注文 {item_count}件',
  '<p>外注ラベルの注文があります。</p><p>注文件数: <strong>{item_count}</strong> 件<br>注文数合計: <strong>{total_order_qty}</strong><br>送信者: {sent_by}<br>送信日時: {sent_at}</p>{item_table}<p>添付: 現品票PDF {attachment_count} 枚（{attachment_names}）</p><p>Smart-EMAP マスタ管理</p>',
  'PRODUCT_LABEL_OUTSOURCE_ORDER',
  'ja',
  '["item_count","total_order_qty","item_table","item_list_text","attachment_count","attachment_names","sent_by","sent_at"]',
  1
)
ON DUPLICATE KEY UPDATE name = VALUES(name), subject = VALUES(subject), body = VALUES(body), variables = VALUES(variables);
