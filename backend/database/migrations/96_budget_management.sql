-- 予算管理（見直し予算 CSV 取込・分析）
-- 受注管理メニュー配下

CREATE TABLE IF NOT EXISTS budget_import_batches (
  id BIGINT NOT NULL AUTO_INCREMENT,
  file_name VARCHAR(255) NOT NULL COMMENT 'アップロードファイル名',
  months_json TEXT NULL COMMENT '取込対象年月 JSON 例: year/month 配列',
  total_rows INT NOT NULL DEFAULT 0 COMMENT 'CSV行数（品番行）',
  matched_rows INT NOT NULL DEFAULT 0 COMMENT '製品マスタ紐付成功行数',
  unmatched_rows INT NOT NULL DEFAULT 0 COMMENT '紐付失敗行数',
  inserted_rows INT NOT NULL DEFAULT 0 COMMENT '新規挿入セル数（年月×品番）',
  updated_rows INT NOT NULL DEFAULT 0 COMMENT '上書き更新セル数',
  uploaded_by VARCHAR(100) NULL,
  remark VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_budget_import_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='予算CSV取込バッチ';

CREATE TABLE IF NOT EXISTS budget_monthly (
  id BIGINT NOT NULL AUTO_INCREMENT,
  year SMALLINT NOT NULL COMMENT '年',
  month TINYINT NOT NULL COMMENT '月',
  development_code VARCHAR(100) NULL COMMENT '開発コード',
  part_number VARCHAR(50) NOT NULL COMMENT '品番（CSV）',
  product_cd VARCHAR(50) NULL COMMENT '製品CD（末尾1のみ紐付）',
  product_name VARCHAR(100) NULL COMMENT '製品名',
  budget_qty INT NOT NULL DEFAULT 0 COMMENT '予算数量',
  match_status VARCHAR(20) NOT NULL DEFAULT 'unmatched' COMMENT 'matched|unmatched|multi_match',
  import_batch_id BIGINT NULL,
  source_file_name VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_budget_ym_part (year, month, part_number),
  KEY idx_budget_ym (year, month),
  KEY idx_budget_product_cd (product_cd),
  KEY idx_budget_part_number (part_number),
  KEY idx_budget_batch (import_batch_id),
  CONSTRAINT fk_budget_monthly_batch
    FOREIGN KEY (import_batch_id) REFERENCES budget_import_batches (id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月次予算数量（同月同品番は上書き）';

-- メニュー：受注管理 > 予算管理
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_ORDER_BUDGET', '予算管理', m.id, '/erp/order/budget', 'Coin', 4
FROM menus m
WHERE m.code = 'ERP_ORDER'
LIMIT 1;

UPDATE menus child
INNER JOIN menus parent ON parent.code = 'ERP_ORDER'
SET child.name = '予算管理',
    child.path = '/erp/order/budget',
    child.icon = 'Coin',
    child.sort_order = 4,
    child.parent_id = parent.id,
    child.is_active = 1
WHERE child.code = 'ERP_ORDER_BUDGET';

-- 月受注管理と同じロール権限を付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT rmp.role_id, new_menu.id
FROM role_menu_permissions rmp
INNER JOIN menus sibling ON sibling.id = rmp.menu_id AND sibling.code = 'ERP_ORDER_MONTHLY'
INNER JOIN menus new_menu ON new_menu.code = 'ERP_ORDER_BUDGET';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_ORDER_BUDGET';
