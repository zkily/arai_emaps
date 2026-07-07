-- 大量廃棄・保留品 未処理通知メール：処理期限を重要表示
SET NAMES utf8mb4;

UPDATE email_templates
SET
  body = '<p>未処理の大量廃棄・保留品記録があります。</p>{deadline_notice}<p>件数: {item_count} 件<br>合計本数: {total_quantity} 本<br>期限超過: {overdue_count} 件<br>送信者: {sent_by}<br>送信日時: {sent_at}</p>{item_table}<p style="margin-top:16px;font-size:12px;color:#64748b;">※ 保留品は処理期限までに必ず対応してください。期限超過分は至急ご確認をお願いします。</p><p>Smart-EMAP 在庫管理システム</p>',
  variables = '["item_count","total_quantity","overdue_count","item_table","item_list_text","deadline_notice","deadline_notice_text","sent_by","sent_at"]'
WHERE code = 'BULK_DISPOSAL_RETENTION_PENDING';
