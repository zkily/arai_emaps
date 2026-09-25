-- 品質管理 > 設備関係：設備保全管理
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `quality_equipment_maintenance` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `process_code` VARCHAR(20) NOT NULL COMMENT '工程 cutting/chamfering/forming/welding/plating',
  `machine_cd` VARCHAR(50) NULL COMMENT '設備マスタCD（任意）',
  `equipment_name` VARCHAR(100) NOT NULL COMMENT '設備名',
  `asset_no` VARCHAR(50) NULL COMMENT '管理番号',
  `location` VARCHAR(100) NULL COMMENT '設置場所',
  `cycle_days` INT NULL COMMENT '保全周期（日）',
  `note` TEXT NULL COMMENT '備考',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=使用中',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '並び',
  `created_by` VARCHAR(64) NULL COMMENT '登録者',
  `updated_by` VARCHAR(64) NULL COMMENT '更新者',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_qem_process` (`process_code`, `is_active`, `sort_order`),
  KEY `idx_qem_machine` (`machine_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備保全 対象設備';

CREATE TABLE IF NOT EXISTS `quality_equipment_maintenance_records` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `equipment_id` BIGINT NOT NULL COMMENT '設備ID',
  `work_type` VARCHAR(20) NOT NULL COMMENT 'maintenance=保全 repair=修理',
  `status` VARCHAR(20) NOT NULL DEFAULT 'planned' COMMENT 'planned/done/cancelled',
  `planned_date` DATE NULL COMMENT '予定日',
  `actual_date` DATE NULL COMMENT '実施日',
  `title` VARCHAR(200) NULL COMMENT '件名',
  `content` TEXT NULL COMMENT '内容',
  `assignee` VARCHAR(100) NULL COMMENT '担当',
  `note` TEXT NULL COMMENT '備考',
  `created_by` VARCHAR(64) NULL COMMENT '登録者',
  `updated_by` VARCHAR(64) NULL COMMENT '更新者',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_qemr_equipment` (`equipment_id`, `status`),
  KEY `idx_qemr_planned` (`planned_date`),
  KEY `idx_qemr_actual` (`actual_date`),
  CONSTRAINT `fk_qemr_equipment` FOREIGN KEY (`equipment_id`)
    REFERENCES `quality_equipment_maintenance` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備保全 実績・予定';

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_QUALITY_EQUIPMENT_MAINTENANCE', '設備保全管理', m.id,
       '/erp/quality/equipment-maintenance', 'Tools', 2
FROM menus m
WHERE m.code = 'ERP_QUALITY_EQUIPMENT_RELATION'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_QUALITY_EQUIPMENT_RELATION'
SET cfg.name = '設備保全管理',
    cfg.parent_id = parent.id,
    cfg.path = '/erp/quality/equipment-maintenance',
    cfg.icon = 'Tools',
    cfg.sort_order = 2
WHERE cfg.code = 'ERP_QUALITY_EQUIPMENT_MAINTENANCE';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'ERP_QUALITY_EQUIPMENT_RELATION'
INNER JOIN menus child ON child.code = 'ERP_QUALITY_EQUIPMENT_MAINTENANCE';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_QUALITY_EQUIPMENT_MAINTENANCE';
