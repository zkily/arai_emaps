-- 検査新聞紙通知メール：確定者・管理コード・切断機を出さず、製品CD / 製品名 / 計画数のみ
SET NAMES utf8mb4;

UPDATE email_templates
SET
  body = '<p>切断実績が確定されました。以下の製品は最終工程（検査）で<strong>新聞紙を入れて</strong>ください。</p><p>生産日: {production_day}<br>対象製品数: {product_count} 品目<br>計画数合計: {total_quantity} 本</p>{product_table}<p>Smart-EMAP 生産管理システム</p>',
  variables = '["production_day","product_table","product_count","total_quantity"]'
WHERE event_code = 'INSPECTION_NEWSPAPER_ALERT'
   OR code = 'INSPECTION_NEWSPAPER_ALERT';
