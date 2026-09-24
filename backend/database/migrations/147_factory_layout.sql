-- 工場レイアウト（設備・通路・材料置き場）と模擬ステータス
-- 実行例: mysql -u USER -p DB_NAME < backend/database/migrations/147_factory_layout.sql

CREATE TABLE IF NOT EXISTS factory_layouts (
  id INT NOT NULL AUTO_INCREMENT COMMENT '主キー',
  name VARCHAR(100) NOT NULL COMMENT 'レイアウト名',
  canvas_width INT NOT NULL DEFAULT 1600 COMMENT 'キャンバス幅',
  canvas_height INT NOT NULL DEFAULT 900 COMMENT 'キャンバス高さ',
  grid_size INT NOT NULL DEFAULT 20 COMMENT 'グリッドサイズ',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工場レイアウト';

CREATE TABLE IF NOT EXISTS factory_layout_objects (
  id INT NOT NULL AUTO_INCREMENT COMMENT '主キー',
  layout_id INT NOT NULL COMMENT 'factory_layouts.id',
  object_type VARCHAR(20) NOT NULL COMMENT 'machine / aisle / material_zone',
  x INT NOT NULL DEFAULT 0 COMMENT '左上 X',
  y INT NOT NULL DEFAULT 0 COMMENT '左上 Y',
  width INT NOT NULL DEFAULT 80 COMMENT '幅',
  height INT NOT NULL DEFAULT 60 COMMENT '高さ',
  label VARCHAR(100) NOT NULL DEFAULT '' COMMENT '表示名',
  ref_cd VARCHAR(100) NULL COMMENT '設備コードまたは庫位',
  z_index INT NOT NULL DEFAULT 0 COMMENT '重なり順',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (id),
  KEY idx_factory_layout_objects_layout (layout_id),
  CONSTRAINT fk_factory_layout_objects_layout
    FOREIGN KEY (layout_id) REFERENCES factory_layouts (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工場レイアウト上のオブジェクト';

CREATE TABLE IF NOT EXISTS factory_layout_status (
  id INT NOT NULL AUTO_INCREMENT COMMENT '主キー',
  object_id INT NOT NULL COMMENT 'factory_layout_objects.id',
  status VARCHAR(30) NOT NULL COMMENT '状態コード',
  message VARCHAR(500) NULL COMMENT '説明',
  payload JSON NULL COMMENT '追加情報（PLC 用）',
  source VARCHAR(20) NOT NULL DEFAULT 'mock' COMMENT 'mock / plc',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (id),
  UNIQUE KEY uk_factory_layout_status_object (object_id),
  CONSTRAINT fk_factory_layout_status_object
    FOREIGN KEY (object_id) REFERENCES factory_layout_objects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工場レイアウトオブジェクトの状態';

INSERT INTO factory_layouts (name, canvas_width, canvas_height, grid_size)
SELECT '示例工厂', 1600, 900, 20
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM factory_layouts WHERE name = '示例工厂');

INSERT INTO factory_layout_objects (layout_id, object_type, x, y, width, height, label, ref_cd, z_index)
SELECT l.id, v.object_type, v.x, v.y, v.w, v.h, v.label, NULL, v.z_index
FROM factory_layouts l
JOIN (
  SELECT 'machine' AS object_type, 80 AS x, 80 AS y, 140 AS w, 90 AS h, '成型机 A' AS label, 20 AS z_index
  UNION ALL SELECT 'machine', 280, 80, 140, 90, '焊接机 B', 20
  UNION ALL SELECT 'machine', 480, 80, 140, 90, '检查台 C', 20
  UNION ALL SELECT 'aisle', 60, 220, 760, 72, '主通路', 0
  UNION ALL SELECT 'material_zone', 80, 360, 220, 130, '材料置场', 10
) v
WHERE l.name = '示例工厂'
  AND NOT EXISTS (
    SELECT 1 FROM factory_layout_objects o WHERE o.layout_id = l.id
  );

INSERT INTO factory_layout_status (object_id, status, message, source)
SELECT o.id, v.status, v.message, 'mock'
FROM factory_layout_objects o
INNER JOIN factory_layouts l ON l.id = o.layout_id AND l.name = '示例工厂'
INNER JOIN (
  SELECT '成型机 A' AS label, 'running' AS status, '生产中' AS message
  UNION ALL SELECT '焊接机 B', 'idle', '待机'
  UNION ALL SELECT '检查台 C', 'alarm', '温度异常（模拟）'
  UNION ALL SELECT '主通路', 'open', '可通行'
  UNION ALL SELECT '材料置场', 'stocked', '钢材在库'
) v ON v.label = o.label
WHERE NOT EXISTS (
  SELECT 1 FROM factory_layout_status s WHERE s.object_id = o.id
);
