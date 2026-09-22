-- 表示名変更：検査新聞紙通知 → 実績工程通知
SET NAMES utf8mb4;

UPDATE menus
SET name = '実績工程通知'
WHERE code = 'ERP_QUALITY_INSPECTION_NEWSPAPER';

UPDATE notification_settings
SET
  event_name = '実績工程通知',
  description = '切断実績確定時、対象製品があれば検査工程へ新聞紙投入を自動メールで通知'
WHERE event_code = 'INSPECTION_NEWSPAPER_ALERT';

UPDATE email_templates
SET name = '実績工程通知'
WHERE code = 'INSPECTION_NEWSPAPER_ALERT'
   OR event_code = 'INSPECTION_NEWSPAPER_ALERT';
