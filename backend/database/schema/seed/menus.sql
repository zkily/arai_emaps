-- SEED: menus
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `menus` (`id`, `code`, `name`, `parent_id`, `path`, `icon`, `sort_order`, `is_active`) VALUES
(1, 'SYSTEM', 'システム管理', NULL, '/system', 'Setting', 1, 1),
(2, 'ERP', 'ERP', NULL, '/erp', 'Management', 2, 1),
(3, 'APS', 'APS', NULL, '/aps', 'DataAnalysis', 3, 1),
(4, 'MES', 'MES', NULL, '/mes', 'Monitor', 4, 1),
(5, 'SYSTEM_USER', 'ユーザー管理', 1, '/system/users', 'User', 1, 1),
(6, 'SYSTEM_ORG', '組織管理', 1, '/system/organization', 'OfficeBuilding', 2, 1),
(7, 'SYSTEM_ROLE', '権限管理', 1, '/system/roles', 'Lock', 3, 1),
(8, 'ERP_SALES', '販売管理', 2, '/erp/sales', 'Sell', 1, 1),
(9, 'ERP_PURCHASE', '購買管理', 2, '/erp/purchase', 'ShoppingCart', 2, 1),
(10, 'ERP_INVENTORY', '在庫管理', 2, '/erp/inventory', 'Box', 3, 1),
(11, 'ERP_COSTING', '原価・会計', 2, '/erp/costing', 'Coin', 4, 1),
(12, 'APS_PLANNING', '成型計画作成', 16, '/aps/planning', 'Calendar', 2, 1),
(13, 'APS_SCHEDULING', 'スケジューリング', 3, '/aps/scheduling', 'Timer', 4, 1),
(14, 'MES_EXECUTION', '製造実行', 4, '/mes/execution', 'Operation', 1, 1),
(15, 'MES_QUALITY', '品質管理', 4, '/mes/quality', 'DocumentChecked', 2, 1),
(16, 'APS_PRODUCTION_PLAN_CREATE', '生産計画作成', 3, NULL, 'Calendar', 1, 1),
(17, 'APS_CUTTING_PLANNING', '切断計画作成', 16, '/aps/cutting-planning', 'Operation', 1, 1),
(18, 'APS_FORMING_PLAN_LIST', '成型計画一覧', 19, '/aps/planning-list', 'List', 1, 1),
(19, 'APS_PRODUCTION_PLAN_VIEW', '生産計画一覧', 3, NULL, 'List', 2, 1),
(20, 'APS_PLATING_PLANNING', 'メッキ計画作成', 16, '/aps/plating-planning', 'Operation', 4, 1),
(23, 'SYSTEM_DATABASE', 'データベース', 1, NULL, 'Coin', 3, 1),
(24, 'SYSTEM_DB_ORDER_DAILY', 'order_daily', 23, '/system/database/order/daily', 'List', 1, 1),
(25, 'APS_EQUIPMENT_UTILIZATION_MANAGEMENT', '設備稼働管理', 3, NULL, 'Setting', 3, 1),
(26, 'APS_CAPACITY_MATRIX', '設備稼働時間表', 25, '/aps/capacity-matrix', 'Document', 2, 1),
(27, 'ERP_INVENTORY_BULK_DISPOSAL_RETENTION', '大量廃棄・保留品管理', 10, '/erp/inventory/bulk-disposal-retention', 'WarningFilled', 57, 1),
(28, 'ERP_INVENTORY_REPORT', '在庫報告管理', 10, '/erp/inventory/report', 'DataBoard', 58, 1),
(29, 'ERP_INVENTORY_PRODUCTION_REVIEW', '生産検討会資料', 10, '/erp/inventory/production-review', 'Document', 59, 1),
(30, 'ERP_PURCHASE_SUPPLIES', '備品購入', 9, '/erp/purchase/supplies', 'Box', 5, 1),
(31, 'APS_CPSAT', 'CP-SAT最適化', 3, '/aps/cpsat', 'MagicStick', 5, 1),
(32, 'APS_OUTSOURCED_PLATING_PLANNING', '外注メッキ計画作成', 16, '/aps/outsourced-plating-planning', 'Brush', 5, 1),
(33, 'ERP_PURCHASE_SUPPLIED_MATERIAL', '支給材管理', 9, NULL, 'Present', 4, 1),
(34, 'ERP_INVENTORY_SUPPLY_PARTS', '補給品管理', 10, '/erp/inventory/supply-parts', 'Box', 4, 1);

SET FOREIGN_KEY_CHECKS = 1;
