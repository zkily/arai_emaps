-- SEED: notification_settings
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `notification_settings` (`id`, `event_code`, `event_name`, `description`, `in_app_enabled`, `email_enabled`, `slack_enabled`, `line_enabled`, `is_active`, `auto_schedule_enabled`, `auto_schedule_time`, `schedule_config`) VALUES
(1, 'APPROVAL_REQUEST', '承認依頼', '新しい承認依頼が届いた時', 1, 1, 1, 0, 1, 0, NULL, NULL),
(2, 'APPROVAL_COMPLETE', '承認完了', '承認が完了した時', 1, 1, 0, 0, 1, 0, NULL, NULL),
(3, 'APPROVAL_REJECT', '承認却下', '承認が却下された時', 1, 1, 1, 0, 1, 0, NULL, NULL),
(4, 'DELIVERY_ALERT', '納期アラート', '納期が近づいている時', 1, 1, 1, 1, 1, 0, NULL, NULL),
(5, 'STOCK_ALERT', '在庫アラート', '在庫が基準値を下回った時', 1, 1, 1, 0, 1, 0, NULL, NULL),
(6, 'SYSTEM_ERROR', 'システムエラー', 'システムエラーが発生した時', 1, 1, 1, 0, 1, 0, NULL, NULL),
(7, 'CUTTING_ACTUAL_CONFIRMED', '切断実績確定', '切断指示の実績確定完了時', 0, 1, 0, 1, 1, 0, NULL, NULL),
(8, 'CHAMFERING_ACTUAL_CONFIRMED', '面取実績確定', '面取指示の実績確定完了時', 0, 1, 0, 1, 1, 0, NULL, NULL),
(9, 'CUTTING_TRIAL_COMPLETED', '切断試作完了', '切断指示-今日で備考に試作を含み完了済みのデータ', 0, 1, 0, 1, 1, 0, NULL, NULL),
(10, 'INVENTORY_STAGNATION', '在庫停滞アラート', '在庫停滞監視で検出した工程別停滞在庫の通知', 0, 1, 0, 1, 1, 1, '08:00:00', '{\"min_quantity\": 50, \"stable_calendar_days\": 7}'),
(11, 'REPORT_CUTTING_DAILY_ACTUAL', '切断工程実績レポート', '切断工程の実績日報（添付配信）', 0, 1, 0, 0, 1, 0, NULL, NULL),
(12, 'REPORT_INVENTORY_TREND_WEEKLY', '在庫推移レポート', '工程別在庫推移の週次レポート（添付配信）', 0, 1, 0, 0, 1, 0, NULL, NULL),
(13, 'REPORT_PLAN_ACTUAL_MONTHLY', '計画実績対比レポート', '計画と実績の月次対比レポート（添付配信）', 0, 1, 0, 0, 1, 0, NULL, NULL),
(14, 'BULK_DISPOSAL_RETENTION_PENDING', '大量廃棄・保留品 未処理通知', '未処理の大量廃棄・保留品記録を指定担当者へメール通知', 0, 1, 0, 0, 1, 0, NULL, NULL),
(15, 'PRODUCT_LABEL_OUTSOURCE_ORDER', '成型用ラベル 外注注文', '外注区分のラベル注文をメール送信（注文一覧＋現品票PDF添付）', 0, 1, 0, 0, 1, 0, NULL, NULL),
(16, 'PRODUCT_USE_LABEL_OUTSOURCE_ORDER', '製品用ラベル 外注注文', '外注区分の製品用ラベル注文をメール送信（注文一覧＋ラベルPDF添付）', 0, 1, 0, 0, 1, 0, NULL, NULL),
(17, 'REPORT_PLAN_BASELINE_WEEKLY', '生産計画ベースラインレポート', '基準計画と実績の比較PDFを週次添付配信（金曜19:00）', 0, 1, 0, 0, 1, 0, NULL, NULL),
(18, 'INSPECTION_NEWSPAPER_ALERT', '検査通知(防錆)', '切断実績確定時、対象製品があれば検査工程へ新聞紙投入を自動メールで通知', 0, 1, 0, 0, 1, 0, NULL, NULL);

SET FOREIGN_KEY_CHECKS = 1;
