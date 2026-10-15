-- 生産設備能力（切断・面取・成型・溶接）。計算式は生産能力調査の記入例に合わせる。
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `production_equipment_capacity` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `process_cd` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程 cutting/chamfering/forming/welding',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '設備コード',
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '設備名',
  `partner_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'パートナー名',
  `vehicle_model` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '対象車種など',
  `regular_hours` decimal(6, 2) NOT NULL DEFAULT 7.60 COMMENT '定時間 h/直',
  `shift_count` decimal(4, 1) NOT NULL DEFAULT 2.0 COMMENT '直数',
  `overtime_hours` decimal(6, 2) NOT NULL DEFAULT 0.00 COMMENT '残業 h/直',
  `working_days` decimal(5, 1) NOT NULL DEFAULT 22.0 COMMENT '月間稼働日数',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '表示順',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pec_process_machine` (`process_cd`, `machine_cd`),
  KEY `idx_pec_process` (`process_cd`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '生産設備能力ヘッダ' ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `production_equipment_capacity_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `capacity_id` int NOT NULL COMMENT '設備能力ID',
  `line_no` int NOT NULL DEFAULT 0 COMMENT '行番',
  `part_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '部品番号',
  `part_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '部品名',
  `customer_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '取引先名',
  `survey_target` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '調査対象',
  `monthly_qty` decimal(14, 2) NOT NULL DEFAULT 0.00 COMMENT '設定数 個/月',
  `qty_days` decimal(6, 2) NOT NULL DEFAULT 0.00 COMMENT '設定数に対する稼働日数',
  `ct_sec` decimal(10, 3) NOT NULL DEFAULT 0.000 COMMENT 'CT 秒/個',
  `availability_rate` decimal(6, 4) NOT NULL DEFAULT 0.9000 COMMENT '可動率 0-1',
  `first_pass_rate` decimal(6, 4) NOT NULL DEFAULT 0.9900 COMMENT '直行率 0-1',
  `cavity_count` decimal(8, 2) NOT NULL DEFAULT 1.00 COMMENT '取り数',
  `setup_hours` decimal(8, 3) NOT NULL DEFAULT 0.000 COMMENT '段取り h/回',
  `actual_days` decimal(6, 2) NOT NULL DEFAULT 0.00 COMMENT '実生産日数',
  `reference_rate` decimal(10, 2) NULL DEFAULT NULL COMMENT '参照能率 本/H',
  `current_rate` decimal(10, 2) NULL DEFAULT NULL COMMENT '現在能率 本/H',
  `takt1_date` date NULL DEFAULT NULL COMMENT 'タクト1 日付',
  `takt1_ct` decimal(10, 3) NULL DEFAULT NULL COMMENT 'タクト1 実測CT秒',
  `takt1_inspect` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'タクト1 検査',
  `takt1_prep` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'タクト1 準備',
  `takt1_overall` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'タクト1 総合',
  `takt2_date` date NULL DEFAULT NULL COMMENT 'タクト2 日付',
  `takt2_ct` decimal(10, 3) NULL DEFAULT NULL COMMENT 'タクト2 実測CT秒',
  `takt2_inspect` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'タクト2 検査',
  `takt2_prep` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'タクト2 準備',
  `takt2_overall` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'タクト2 総合',
  `remarks` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '備考',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_peci_capacity` (`capacity_id`),
  CONSTRAINT `fk_peci_capacity` FOREIGN KEY (`capacity_id`) REFERENCES `production_equipment_capacity` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '生産設備能力 品目' ROW_FORMAT = Dynamic;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'ERP_PRODUCTION_EQUIPMENT_CAPACITY', '生産設備能力', p.id, NULL, 'Odometer', 9, 1
FROM menus p
WHERE p.code = 'ERP_PRODUCTION'
LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'ERP_PRODUCTION_EQ_CAP_CUTTING', '切断設備', p.id, '/erp/production/equipment-capacity/cutting', 'Crop', 1, 1
FROM menus p
WHERE p.code = 'ERP_PRODUCTION_EQUIPMENT_CAPACITY'
LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'ERP_PRODUCTION_EQ_CAP_CHAMFERING', '面取設備', p.id, '/erp/production/equipment-capacity/chamfering', 'Operation', 2, 1
FROM menus p
WHERE p.code = 'ERP_PRODUCTION_EQUIPMENT_CAPACITY'
LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'ERP_PRODUCTION_EQ_CAP_FORMING', '成型設備', p.id, '/erp/production/equipment-capacity/forming', 'Box', 3, 1
FROM menus p
WHERE p.code = 'ERP_PRODUCTION_EQUIPMENT_CAPACITY'
LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'ERP_PRODUCTION_EQ_CAP_WELDING', '溶接設備', p.id, '/erp/production/equipment-capacity/welding', 'Connection', 4, 1
FROM menus p
WHERE p.code = 'ERP_PRODUCTION_EQUIPMENT_CAPACITY'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_PRODUCTION'
SET cfg.name = '生産設備能力',
    cfg.parent_id = parent.id,
    cfg.path = NULL,
    cfg.icon = 'Odometer',
    cfg.sort_order = 9,
    cfg.is_active = 1
WHERE cfg.code = 'ERP_PRODUCTION_EQUIPMENT_CAPACITY';

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_PRODUCTION_EQUIPMENT_CAPACITY'
SET cfg.name = '切断設備',
    cfg.parent_id = parent.id,
    cfg.path = '/erp/production/equipment-capacity/cutting',
    cfg.icon = 'Crop',
    cfg.sort_order = 1,
    cfg.is_active = 1
WHERE cfg.code = 'ERP_PRODUCTION_EQ_CAP_CUTTING';

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_PRODUCTION_EQUIPMENT_CAPACITY'
SET cfg.name = '面取設備',
    cfg.parent_id = parent.id,
    cfg.path = '/erp/production/equipment-capacity/chamfering',
    cfg.icon = 'Operation',
    cfg.sort_order = 2,
    cfg.is_active = 1
WHERE cfg.code = 'ERP_PRODUCTION_EQ_CAP_CHAMFERING';

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_PRODUCTION_EQUIPMENT_CAPACITY'
SET cfg.name = '成型設備',
    cfg.parent_id = parent.id,
    cfg.path = '/erp/production/equipment-capacity/forming',
    cfg.icon = 'Box',
    cfg.sort_order = 3,
    cfg.is_active = 1
WHERE cfg.code = 'ERP_PRODUCTION_EQ_CAP_FORMING';

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_PRODUCTION_EQUIPMENT_CAPACITY'
SET cfg.name = '溶接設備',
    cfg.parent_id = parent.id,
    cfg.path = '/erp/production/equipment-capacity/welding',
    cfg.icon = 'Connection',
    cfg.sort_order = 4,
    cfg.is_active = 1
WHERE cfg.code = 'ERP_PRODUCTION_EQ_CAP_WELDING';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, n.id
FROM role_menu_permissions rmp
INNER JOIN menus src ON src.id = rmp.menu_id AND src.code LIKE 'ERP_PRODUCTION%'
INNER JOIN menus n ON n.code IN (
  'ERP_PRODUCTION_EQUIPMENT_CAPACITY',
  'ERP_PRODUCTION_EQ_CAP_CUTTING',
  'ERP_PRODUCTION_EQ_CAP_CHAMFERING',
  'ERP_PRODUCTION_EQ_CAP_FORMING',
  'ERP_PRODUCTION_EQ_CAP_WELDING'
);

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT r.id, m.id
FROM roles r
INNER JOIN menus m ON m.code IN (
  'ERP_PRODUCTION_EQUIPMENT_CAPACITY',
  'ERP_PRODUCTION_EQ_CAP_CUTTING',
  'ERP_PRODUCTION_EQ_CAP_CHAMFERING',
  'ERP_PRODUCTION_EQ_CAP_FORMING',
  'ERP_PRODUCTION_EQ_CAP_WELDING'
)
WHERE r.name = '管理者';
