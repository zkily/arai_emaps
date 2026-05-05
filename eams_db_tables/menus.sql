SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for menus
-- ----------------------------
DROP TABLE IF EXISTS `menus`;
CREATE TABLE `menus`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'メニューコード',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'メニュー名',
  `parent_id` int NULL DEFAULT NULL COMMENT '親メニューID',
  `path` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ルートパス',
  `icon` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'アイコン名',
  `sort_order` int NULL DEFAULT 0 COMMENT '表示順序',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code` ASC) USING BTREE,
  INDEX `idx_menus_parent`(`parent_id` ASC) USING BTREE,
  CONSTRAINT `fk_menus_parent` FOREIGN KEY (`parent_id`) REFERENCES `menus` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 176 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'メニューテーブル' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of menus
-- ----------------------------
INSERT INTO `menus` VALUES (1, 'SYSTEM', 'システム管理', NULL, NULL, 'Setting', 5, 1, '2026-02-05 14:00:55');
INSERT INTO `menus` VALUES (2, 'ERP', 'ERP管理メニュー', NULL, NULL, 'Management', 1, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (3, 'APS', 'APS管理メニュー', NULL, NULL, 'DataAnalysis', 2, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (4, 'MES', 'MES管理メニュー', NULL, NULL, 'Monitor', 3, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (6, 'SYSTEM_USER', 'ユーザー・組織', 1, NULL, 'User', 1, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (7, 'SYSTEM_ORG', '組織・部門管理', 6, '/system/organization', NULL, 2, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (8, 'SYSTEM_ROLE', '権限・ロール管理', 6, '/system/roles', NULL, 3, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (9, 'ERP_SALES', '販売管理', 2, '/erp/sales', 'Sell', 1, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (10, 'ERP_PURCHASE', '購買・外注管理', 2, '/erp/purchase', 'ShoppingCart', 3, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (11, 'ERP_INVENTORY', '在庫管理', 2, '/erp/inventory', 'Box', 5, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (12, 'ERP_COSTING', '原価・財務連携', 2, '/erp/costing', 'Coin', 7, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (13, 'APS_PLANNING', '成型計画作成', 154, '/aps/planning', NULL, 1, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (14, 'APS_SCHEDULING', 'スケジューリング', 3, '/aps/scheduling', NULL, 2, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (15, 'MES_EXECUTION', '製造実行', 4, '/mes/execution', NULL, 1, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (16, 'MES_QUALITY', '品質管理', 4, '/mes/quality', NULL, 2, 1, '2026-02-05 14:03:46');
INSERT INTO `menus` VALUES (17, 'DASHBOARD', 'ダッシュボード', NULL, '/dashboard', 'HomeFilled', 0, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (18, 'ERP_SALES_HOME', '販売ホーム', 9, '/erp/sales', NULL, 0, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (19, 'ERP_SALES_QUOTATION', '見積管理', 9, '/erp/sales/quotation', NULL, 1, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (20, 'ERP_SALES_ORDERS', '受注一覧', 9, '/erp/sales/orders', NULL, 2, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (21, 'ERP_SALES_EDI', 'EDI取込', 9, '/erp/sales/edi-import', NULL, 3, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (22, 'ERP_SALES_SHIPPING', '出荷指示', 9, '/erp/sales/shipping', NULL, 7, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (23, 'ERP_SALES_RECORDING', '売上計上', 9, '/erp/sales/recording', NULL, 8, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (24, 'ERP_SALES_RETURNS', '返品管理(RMA)', 9, '/erp/sales/returns', NULL, 11, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (25, 'ERP_PURCHASE_HOME', '購買ホーム', 10, '/erp/purchase', NULL, 0, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (26, 'ERP_PURCHASE_ORDERS', '発注一覧', 10, '/erp/purchase/orders', NULL, 1, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (27, 'ERP_PURCHASE_RFQ', '見積依頼(RFQ)', 10, '/erp/purchase/rfq', NULL, 2, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (28, 'ERP_PURCHASE_ARRIVAL', '入荷予定管理', 10, '/erp/purchase/arrival', NULL, 6, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (29, 'ERP_PURCHASE_RECEIPT', '受入登録', 10, '/erp/purchase/receipt', NULL, 7, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (30, 'ERP_PURCHASE_INVOICE', '請求書照合', 10, '/erp/purchase/invoice-matching', NULL, 9, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (31, 'ERP_INVENTORY_HOME', '在庫ホーム', 11, '/erp/inventory', NULL, 0, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (32, 'ERP_INVENTORY_LIST', '在庫照会', 11, '/erp/inventory/list', NULL, 1, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (33, 'ERP_INVENTORY_TX', '入出庫履歴', 11, '/erp/inventory/transactions', NULL, 2, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (34, 'ERP_INVENTORY_MOVEMENT', '入出庫移動', 11, '/erp/inventory/movement', NULL, 3, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (35, 'ERP_INVENTORY_STOCKTAKING', '棚卸管理', 11, '/erp/inventory/stocktaking', NULL, 6, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (36, 'ERP_INVENTORY_DEAD', '滞留在庫アラート', 11, '/erp/inventory/dead-stock', NULL, 7, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (37, 'ERP_INVENTORY_ABC', 'ABC分析', 11, '/erp/inventory/abc-analysis', NULL, 8, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (38, 'ERP_COSTING_HOME', '原価・会計ホーム', 12, '/erp/costing', NULL, 0, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (39, 'ERP_COSTING_STANDARD', '標準原価計算', 12, '/erp/costing/standard', NULL, 1, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (40, 'ERP_COSTING_ACTUAL', '実際原価計算', 12, '/erp/costing/actual', NULL, 2, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (41, 'ERP_COSTING_VARIANCE', '原価差異分析', 12, '/erp/costing/variance', NULL, 3, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (42, 'ERP_COSTING_BILLING', '請求管理(AR)', 12, '/erp/costing/billing', NULL, 10, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (43, 'ERP_COSTING_PAYMENT', '支払管理(AP)', 12, '/erp/costing/payment', NULL, 11, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (44, 'ERP_ORDER', '受注管理', 2, '/erp/order', 'Document', 2, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (45, 'ERP_ORDER_HOME', '受注ホーム', 44, '/erp/order', NULL, 0, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (46, 'ERP_ORDER_MONTHLY', '月受注管理', 44, '/erp/order/monthly', NULL, 1, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (47, 'ERP_ORDER_DAILY', '日受注管理', 44, '/erp/order/daily', NULL, 2, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (48, 'ERP_ORDER_DASHBOARD', '受注ダッシュボード', 44, '/erp/order/dashboard', NULL, 3, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (49, 'ERP_ORDER_KPI', 'KPIダッシュボード', 44, '/erp/order/kpi', NULL, 4, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (50, 'ERP_ORDER_DAILY_HIST', '日別受注履歴', 44, '/erp/order/daily-history', NULL, 5, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (51, 'ERP_ORDER_CUSTOMER_HIST', '顧客別受注履歴', 44, '/erp/order/customer-history', NULL, 6, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (52, 'ERP_ORDER_DEST_HIST', '納入先別受注履歴', 44, '/erp/order/destination-history', NULL, 3, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (53, 'ERP_ORDER_COMPARISON', '受注履歴比較', 44, '/erp/order/comparison', NULL, 8, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (54, 'ERP_ORDER_PRINT', '受注印刷', 44, '/erp/order/print', NULL, 9, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (55, 'ERP_SUPPLIER', '仕入先管理', 2, '/erp/supplier', 'User', 6, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (56, 'SYSTEM_HOME', 'システムホーム', 6, '/system', NULL, 0, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (57, 'SYSTEM_USERS', 'ユーザー管理', 6, '/system/users', NULL, 1, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (58, 'SYSTEM_SETTINGS', 'システム設定', 1, NULL, 'Tools', 2, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (59, 'SYSTEM_NUMBERING', '採番ルール管理', 58, '/system/numbering', NULL, 1, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (60, 'SYSTEM_WORKFLOW', 'ワークフロー設定', 58, '/system/workflow', NULL, 2, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (61, 'SYSTEM_NOTIFICATION', '通知センター', 58, '/system/notification', NULL, 3, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (62, 'SYSTEM_LOGS', 'システムログ', 58, '/system/logs', NULL, 4, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (63, 'SYSTEM_DATA', 'データ管理', 58, '/system/data', NULL, 5, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (64, 'SYSTEM_MENUS', 'メニュー管理', 58, '/system/menus', NULL, 6, 1, '2026-02-06 08:13:48');
INSERT INTO `menus` VALUES (65, 'MASTER', 'マスタ管理', NULL, NULL, 'Collection', 4, 1, '2026-02-09 09:55:49');
INSERT INTO `menus` VALUES (66, 'MASTER_LIST', 'マスタ', 65, NULL, NULL, 1, 1, '2026-02-09 09:55:49');
INSERT INTO `menus` VALUES (67, 'MASTER_PRODUCT', '製品マスタ', 66, '/master/product', NULL, 1, 1, '2026-02-09 09:55:49');
INSERT INTO `menus` VALUES (68, 'MASTER_MATERIAL', '材料マスタ', 66, '/master/material', NULL, 2, 1, '2026-02-09 09:55:49');
INSERT INTO `menus` VALUES (69, 'MASTER_SUPPLIER', '仕入先マスタ', 66, '/master/supplier', NULL, 3, 1, '2026-02-09 09:55:49');
INSERT INTO `menus` VALUES (70, 'MASTER_PROCESS_ROUTE', '工程ルートマスタ', 66, '/master/process-route', NULL, 5, 1, '2026-02-09 09:55:49');
INSERT INTO `menus` VALUES (71, 'MASTER_BOM', 'BOM', 65, NULL, NULL, 2, 1, '2026-02-09 09:55:49');
INSERT INTO `menus` VALUES (72, 'ERP_SALES_FORECAST', '内示・フォーキャスト', 9, '/erp/sales/forecast', NULL, 4, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (73, 'ERP_SALES_CREDIT', '与信管理', 9, '/erp/sales/credit', NULL, 5, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (74, 'ERP_SALES_CONTRACT', '契約単価管理', 9, '/erp/sales/contract-pricing', NULL, 6, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (75, 'ERP_SALES_INVOICE', '請求書発行', 9, '/erp/sales/invoice', NULL, 9, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (76, 'ERP_SALES_CORRECTION', '赤黒訂正処理', 9, '/erp/sales/return-correction', NULL, 10, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (77, 'ERP_PURCHASE_SUBCONTRACT', '外注加工指示', 10, '/erp/purchase/subcontract-order', NULL, 3, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (78, 'ERP_PURCHASE_SUPPLY', '有償/無償支給', 10, '/erp/purchase/material-supply', NULL, 4, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (79, 'ERP_PURCHASE_SUB_INV', '外注先在庫', 10, '/erp/purchase/subcontract-inventory', NULL, 5, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (80, 'ERP_PURCHASE_INSPECTION', '受入検査', 10, '/erp/purchase/inspection', NULL, 8, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (81, 'ERP_PURCHASE_PAY_SCHEDULE', '支払予定表', 10, '/erp/purchase/payment-schedule', NULL, 10, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (82, 'ERP_PURCHASE_BANK', 'FBデータ作成', 10, '/erp/purchase/bank-transfer', NULL, 11, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (83, 'ERP_INVENTORY_LOCATION', 'ロケーション管理', 11, '/erp/inventory/location', NULL, 2, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (84, 'ERP_INVENTORY_STOCK_ENTRY', '在庫登録管理', 11, '/erp/inventory/stock-entry', NULL, 3, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (85, 'ERP_INVENTORY_STOCK_TX_LOG', '在庫取引記録', 11, '/erp/inventory/stock-transaction-logs', NULL, 9, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (86, 'ERP_PRODUCTION', '生産管理', 2, '/erp/production', 'Setting', 6, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (87, 'ERP_PRODUCTION_HOME', '生産ホーム', 86, '/erp/production', NULL, 0, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (88, 'ERP_PRODUCTION_PLANNING', '生産計画', 86, '/erp/production/data-management', NULL, 5, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (89, 'ERP_PRODUCTION_DATA', '生産データ管理', 88, '/erp/production/data-management', NULL, 1, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (90, 'ERP_PRODUCTION_BASELINE', '計画ベースライン', 88, '/erp/production/plan-baseline', NULL, 2, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (91, 'ERP_PRODUCTION_INSTRUCTION', '生産指示', 86, '/erp/production/instruction', NULL, 6, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (92, 'ERP_PRODUCTION_INSTR_CUTTING', '切断・面取指示', 91, '/erp/production/instruction/cutting', NULL, 1, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (93, 'ERP_PRODUCTION_INSTR_SURFACE', '面取指示', 91, '/erp/production/instruction/surface', NULL, 2, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (94, 'ERP_PRODUCTION_INSTR_FORMING', '成型指示', 91, '/erp/production/instruction/forming', NULL, 3, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (95, 'ERP_PRODUCTION_INSTR_WELDING', '溶接指示', 91, '/erp/production/instruction/welding', NULL, 4, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (96, 'ERP_PRODUCTION_INSTR_PLATING', 'メッキ指示', 91, '/erp/production/instruction/plating', NULL, 5, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (97, 'ERP_PRODUCTION_RESULT', '生産実績', 86, '/erp/production/actual-management', NULL, 8, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (98, 'ERP_PRODUCTION_ACTUAL', '生産実績管理', 97, '/erp/production/actual-management', NULL, 1, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (99, 'ERP_PRODUCTION_COMPLETE', '完成報告', 97, '/erp/production/completion', NULL, 2, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (100, 'ERP_PRODUCTION_CONSUME', '材料消費実績', 97, '/erp/production/consumption', NULL, 2, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (101, 'ERP_COSTING_ALLOCATION', '配賦計算', 12, '/erp/costing/allocation', NULL, 4, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (102, 'ERP_COSTING_WIP', '仕掛品(WIP)評価', 12, '/erp/costing/wip', NULL, 5, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (103, 'ERP_COSTING_EQUIPMENT', '設備台帳', 12, '/erp/costing/equipment', NULL, 6, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (104, 'ERP_COSTING_DEPRECIATION', '減価償却計算', 12, '/erp/costing/depreciation', NULL, 7, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (105, 'ERP_COSTING_JOURNAL', '自動仕訳生成', 12, '/erp/costing/journal', NULL, 8, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (106, 'ERP_COSTING_ACCT_EXPORT', '会計ソフト出力', 12, '/erp/costing/accounting-export', NULL, 9, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (107, 'ERP_SHIPPING', '出荷管理', 2, '/erp/shipping', 'Van', 8, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (108, 'ERP_SHIPPING_HOME', '出荷ホーム', 107, '/erp/shipping', NULL, 0, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (109, 'ERP_SHIPPING_LIST', '出荷構成表管理', 107, '/erp/shipping/list', NULL, 1, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (110, 'ERP_SHIPPING_REPORT', '出荷報告書管理', 107, '/erp/shipping/report', NULL, 2, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (111, 'ERP_SHIPPING_OVERVIEW', '出荷予定表発行', 107, '/erp/shipping/overview', NULL, 3, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (112, 'ERP_SHIPPING_CONFIRM', '出荷確認リスト', 107, '/erp/shipping/confirm', NULL, 4, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (113, 'ERP_SHIPPING_WELDING', '溶接出荷管理', 107, '/erp/shipping/welding', NULL, 5, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (114, 'ERP_SHIPPING_PICKING', 'ピッキング管理', 107, '/erp/shipping/picking', NULL, 6, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (115, 'ERP_SHIPPING_INVENTORY_SHORTAGE', '倉庫在庫管理', 107, '/erp/shipping/inventory-shortage', NULL, 7, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (116, 'ERP_SHIPPING_ABC', 'ABC分析', 107, '/erp/shipping/abc-analysis', NULL, 8, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (117, 'ERP_SHIPPING_INVENTORY_KPI', '在庫KPI・アラート', 107, '/erp/shipping/inventory-kpi', NULL, 9, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (118, 'MASTER_HOME', 'マスタホーム', 66, '/master', NULL, 0, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (119, 'MASTER_PROCESS', '工程マスタ', 66, '/master/process', NULL, 4, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (120, 'MASTER_PRODUCT_PROCESS_ROUTE', '製品別工程ルートマスタ', 66, '/master/product-process-route', NULL, 6, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (121, 'MASTER_CUSTOMER', '顧客マスタ', 66, '/master/customer', NULL, 7, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (122, 'MASTER_CARRIER', '運送便マスタ', 66, '/master/carrier', NULL, 8, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (123, 'MASTER_MACHINE', '設備マスタ', 66, '/master/machine', NULL, 9, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (124, 'MASTER_DESTINATION', '納入先マスタ', 66, '/master/destination', NULL, 10, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (125, 'MASTER_DESTINATION_HOLIDAY', '納入先休日設定', 66, '/master/destination/holiday', NULL, 11, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (126, 'MASTER_BOM_HOME', 'BOMホーム', 71, '/master/bom', NULL, 0, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (127, 'MASTER_PRODUCT_PROCESS_BOM', '製品工程BOM', 71, '/master/bom/product-process', NULL, 1, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (128, 'MASTER_PRODUCT_MACHINE_CONFIG', '製品機器設定', 71, '/master/bom/product-machine-config', NULL, 2, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (129, 'MASTER_EQUIPMENT_EFFICIENCY', '設備能率管理', 71, '/master/bom/equipment-efficiency', NULL, 3, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (130, 'SYSTEM_FILE_WATCHER', 'ファイル監視設定', 58, '/system/file-watcher', NULL, 7, 1, '2026-02-20 09:43:29');
INSERT INTO `menus` VALUES (131, 'ERP_PURCHASE_OUTSOURCING', '外注管理', 10, '/erp/purchase/outsourcing', 'OfficeBuilding', 0, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (132, 'ERP_OUTSOURCING_HOME', '外注ホーム', 131, '/erp/purchase/outsourcing', NULL, 0, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (133, 'ERP_OUTSOURCING_PLATING_ORDER', '外注メッキ注文', 131, '/erp/purchase/outsourcing/plating-order', NULL, 2, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (134, 'ERP_OUTSOURCING_PLATING_RECEIVING', '外注メッキ受入', 131, '/erp/purchase/outsourcing/plating-receiving', NULL, 3, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (135, 'ERP_OUTSOURCING_WELDING_ORDER', '外注溶接注文', 131, '/erp/purchase/outsourcing/welding-order', NULL, 4, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (136, 'ERP_OUTSOURCING_WELDING_RECEIVING', '外注溶接受入', 131, '/erp/purchase/outsourcing/welding-receiving', NULL, 5, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (137, 'ERP_OUTSOURCING_SUPPLIERS', '外注先マスタ', 131, '/erp/purchase/outsourcing/suppliers', NULL, 6, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (138, 'ERP_OUTSOURCING_PROCESS_PRODUCTS', '外注工程製品', 131, '/erp/purchase/outsourcing/process-products', NULL, 7, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (139, 'ERP_OUTSOURCING_STOCK', '外注在庫', 131, '/erp/purchase/outsourcing/stock', NULL, 8, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (140, 'ERP_OUTSOURCING_SUPPLIED_STOCK', '支給材料在庫', 131, '/erp/purchase/outsourcing/supplied-material-stock', NULL, 9, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (141, 'ERP_OUTSOURCING_USAGE', '使用数管理', 131, '/erp/purchase/outsourcing/usage', NULL, 10, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (142, 'ERP_OUTSOURCING_MATERIAL_ISSUE', '支給材料出庫', 131, '/erp/purchase/outsourcing/material-issue', NULL, 11, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (143, 'ERP_INVENTORY_STOCKTAKE', '棚卸管理', 11, '/erp/inventory/stocktake', NULL, 2, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (144, 'ERP_INVENTORY_STOCKTAKE_HOME', '棚卸管理ホーム', 143, '/erp/inventory/stocktake', 'HomeFilled', 0, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (145, 'ERP_INVENTORY_STOCKTAKE_LIST', '棚卸リスト一覧', 143, '/erp/inventory/stocktake/list', 'List', 1, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (146, 'ERP_INVENTORY_STOCKTAKE_ENTRY', '棚卸登録', 143, '/erp/inventory/stocktake/entry', 'DocumentAdd', 2, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (147, 'ERP_INVENTORY_STOCKTAKE_STATISTICS', '棚卸分析', 143, '/erp/inventory/stocktake/statistics', 'DataAnalysis', 3, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (148, 'ERP_INVENTORY_STOCKTAKE_VALUE', '棚卸金額管理', 143, '/erp/inventory/stocktake/value', 'Coin', 4, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (149, 'ERP_INVENTORY_STOCKTAKE_CARRYOVER', '棚卸繰越管理', 143, '/erp/inventory/stocktake/carryover', 'Tools', 5, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (150, 'APS_CAPACITY', '設備稼働設定', 3, '/aps/capacity', NULL, 3, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (151, 'APS_DAILY_REPORT', '日別設備計画表', 3, '/aps/daily-report', NULL, 5, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (152, 'APS_BATCH_PLANS', 'APSロット計画', 3, '/aps/batch-plans', NULL, 6, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (153, 'MASTER_MATERIAL_INSPECTION', '材料検品マスタ', 66, '/master/material-inspection', NULL, 3, 1, '2026-03-27 13:18:22');
INSERT INTO `menus` VALUES (154, 'APS_PRODUCTION_PLAN_CREATE', '生産計画作成', 3, NULL, 'Calendar', 1, 1, '2026-03-30 08:00:42');
INSERT INTO `menus` VALUES (155, 'APS_CUTTING_PLANNING', '切断計画作成', 154, '/aps/cutting-planning', 'Operation', 2, 1, '2026-03-30 08:01:10');
INSERT INTO `menus` VALUES (156, 'ERP_PRODUCTION_PLAN_SCHEDULES', '生産スケジュール', 88, '/erp/production/plan-schedules', NULL, 3, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (157, 'ERP_PRODUCTION_REQUIREMENTS', '生産需要量', 86, '/erp/production-requirements/material', NULL, 6, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (158, 'ERP_PRODUCTION_MAT_REQ', '材料需要量', 157, '/erp/production-requirements/material', NULL, 1, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (159, 'ERP_PRODUCTION_COMPONENT_REQ', '部品需要量', 157, '/erp/production-requirements/component', NULL, 2, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (160, 'ERP_QUALITY', '品質管理', 2, '/erp/quality', 'CircleCheck', 9, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (161, 'ERP_QUALITY_MATERIAL', '材料受入履歴', 160, '/erp/quality/material-association/receiving-history', NULL, 1, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (162, 'ERP_QUALITY_MATERIAL_TOLERANCE', '材料公差管理', 160, '/erp/quality/material-association/tolerance-management', NULL, 1, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (163, 'ERP_QUALITY_MATERIAL_CUTTING', '材料使用取込', 160, '/erp/quality/material-association/cutting-logs', NULL, 1, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (164, 'ERP_QUALITY_PRODUCT_MATERIAL', '製品材料照会', 160, '/erp/quality/material-association/product-material', NULL, 1, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (165, 'ERP_QUALITY_PRODUCT_MATERIAL_HELP', '製品材料照会 操作説明', 160, '/erp/quality/material-association/product-material/help', NULL, 1, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (166, 'ERP_QUALITY_PRODUCT', '製品関連', 160, '/erp/quality/product-association', NULL, 2, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (167, 'APS_PRODUCTION_PLAN_VIEW', '生産計画一覧', 3, NULL, 'List', 2, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (168, 'APS_FORMING_PLAN_LIST', '成型計画一覧', 167, '/aps/planning-list', 'List', 1, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (169, 'APS_CAPACITY_MATRIX', '設備稼働時間表', 3, '/aps/capacity-matrix', NULL, 4, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (170, 'MES_PRODUCTION_INSTRUCTION', '生産指示', 4, NULL, NULL, 1, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (171, 'MES_FORMING_INSTRUCTION', '成型指示', 170, '/mes/instruction/forming', NULL, 1, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (172, 'MASTER_PART', '部品マスタ', 66, '/master/part', NULL, 3, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (173, 'MASTER_PRODUCT_BOM_DETAIL', '製品BOM表管理', 71, '/master/bom/product-bom', NULL, 4, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (174, 'MASTER_PROCESS_PROCESSING_FEE', '工程加工費マスタ', 66, '/master/bom/process-processing-fee', NULL, 7, 1, '2026-04-16 13:02:35');
INSERT INTO `menus` VALUES (175, 'MASTER_UNIT_PRICE', '工程別標準原価', 71, '/master/bom/product-unit-price', NULL, 6, 1, '2026-04-16 13:02:35');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
