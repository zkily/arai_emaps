-- 工場レイアウト：塗り・枠線・不透明度。サンプル表示名を日本語に揃える。
ALTER TABLE factory_layout_objects
  ADD COLUMN fill_color VARCHAR(7) NULL COMMENT '塗り色 #RRGGBB。NULL は状態色',
  ADD COLUMN border_color VARCHAR(7) NULL COMMENT '枠線色 #RRGGBB',
  ADD COLUMN opacity INT NOT NULL DEFAULT 100 COMMENT '不透明度 0-100';

UPDATE factory_layouts SET name = 'サンプル工場' WHERE name = '示例工厂';

UPDATE factory_layout_objects SET label = '成形機 A' WHERE label = '成型机 A';
UPDATE factory_layout_objects SET label = '溶接機 B' WHERE label = '焊接机 B';
UPDATE factory_layout_objects SET label = '検査台 C' WHERE label = '检查台 C';
UPDATE factory_layout_objects SET label = '材料置き場' WHERE label = '材料置场';

UPDATE factory_layout_status s
INNER JOIN factory_layout_objects o ON o.id = s.object_id
SET s.message = CASE o.label
  WHEN '成形機 A' THEN '生産中'
  WHEN '溶接機 B' THEN '待機'
  WHEN '検査台 C' THEN '温度異常（模擬）'
  WHEN '主通路' THEN '通行可'
  WHEN '材料置き場' THEN '鋼材在庫'
  ELSE s.message
END
WHERE o.label IN ('成形機 A', '溶接機 B', '検査台 C', '主通路', '材料置き場');

UPDATE factory_layout_status SET message = '待機' WHERE message = '待机';
UPDATE factory_layout_status SET message = '温度異常（模擬）' WHERE message = '温度异常（模拟）';
UPDATE factory_layout_status SET message = '生産中' WHERE message = '生产中';
UPDATE factory_layout_status SET message = '通行可' WHERE message = '可通行';
UPDATE factory_layout_status SET message = '鋼材在庫' WHERE message = '钢材在库';
