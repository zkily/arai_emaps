/**
 * メニュー定義（単一ソース）
 * 新規ルート追加時はここに1件追加し、管理画面で「ルート定義から取り込み」を実行すると menus テーブルに反映される
 */
export interface MenuConfigItem {
  code: string
  name: string
  path?: string
  icon?: string
  parentCode?: string
  sortOrder: number
}

/** 全メニュー定義（親→子の順で並べる） */
export const menuConfig: MenuConfigItem[] = [
  { code: 'DASHBOARD', name: 'ダッシュボード', path: '/dashboard', icon: 'HomeFilled', sortOrder: 0 },
  { code: 'ERP', name: '総合管理メニュー', icon: 'Management', sortOrder: 1 },

  // ===== 1. 販売管理 (Sales / SD) =====
  { code: 'ERP_SALES', name: '販売管理', path: '/erp/sales', icon: 'Sell', parentCode: 'ERP', sortOrder: 1 },
  { code: 'ERP_SALES_HOME', name: '販売ホーム', path: '/erp/sales', parentCode: 'ERP_SALES', sortOrder: 0 },
  { code: 'ERP_SALES_QUOTATION', name: '見積管理', path: '/erp/sales/quotation', parentCode: 'ERP_SALES', sortOrder: 1 },
  { code: 'ERP_SALES_ORDERS', name: '受注一覧', path: '/erp/sales/orders', parentCode: 'ERP_SALES', sortOrder: 2 },
  { code: 'ERP_SALES_FORECAST', name: '内示・フォーキャスト', path: '/erp/sales/forecast', parentCode: 'ERP_SALES', sortOrder: 4 },
  { code: 'ERP_SALES_CREDIT', name: '与信管理', path: '/erp/sales/credit', parentCode: 'ERP_SALES', sortOrder: 5 },
  { code: 'ERP_SALES_CONTRACT', name: '契約単価管理', path: '/erp/sales/contract-pricing', parentCode: 'ERP_SALES', sortOrder: 6 },
  { code: 'ERP_SALES_SHIPPING', name: '出荷指示', path: '/erp/sales/shipping', parentCode: 'ERP_SALES', sortOrder: 7 },
  { code: 'ERP_SALES_RECORDING', name: '売上計上', path: '/erp/sales/recording', parentCode: 'ERP_SALES', sortOrder: 8 },
  { code: 'ERP_SALES_INVOICE', name: '請求書発行', path: '/erp/sales/invoice', parentCode: 'ERP_SALES', sortOrder: 9 },
  { code: 'ERP_SALES_CORRECTION', name: '赤黒訂正処理', path: '/erp/sales/return-correction', parentCode: 'ERP_SALES', sortOrder: 10 },
  { code: 'ERP_SALES_RETURNS', name: '返品管理(RMA)', path: '/erp/sales/returns', parentCode: 'ERP_SALES', sortOrder: 11 },

  // ===== 受注管理 (Order Management) =====
  { code: 'ERP_ORDER', name: '受注管理', path: '/erp/order', icon: 'Document', parentCode: 'ERP', sortOrder: 2 },
  { code: 'ERP_ORDER_HOME', name: '受注ホーム', path: '/erp/order', parentCode: 'ERP_ORDER', sortOrder: 0 },
  { code: 'ERP_ORDER_MONTHLY', name: '月受注管理', path: '/erp/order/monthly', parentCode: 'ERP_ORDER', sortOrder: 1 },
  { code: 'ERP_ORDER_DAILY', name: '日受注管理', path: '/erp/order/daily', parentCode: 'ERP_ORDER', sortOrder: 2 },

  // ===== 2. 購買・外注管理 (Procurement & Subcontracting) =====
  { code: 'ERP_PURCHASE', name: '購買・外注管理', path: '/erp/purchase', icon: 'ShoppingCart', parentCode: 'ERP', sortOrder: 3 },
  { code: 'ERP_PURCHASE_HOME', name: '購買ホーム', path: '/erp/purchase', parentCode: 'ERP_PURCHASE', sortOrder: 0 },
  { code: 'ERP_PURCHASE_ORDERS', name: '発注一覧', path: '/erp/purchase/orders', parentCode: 'ERP_PURCHASE', sortOrder: 1 },
  { code: 'ERP_PURCHASE_RFQ', name: '見積依頼(RFQ)', path: '/erp/purchase/rfq', parentCode: 'ERP_PURCHASE', sortOrder: 2 },
  { code: 'ERP_PURCHASE_SUBCONTRACT', name: '外注加工指示', path: '/erp/purchase/subcontract-order', parentCode: 'ERP_PURCHASE', sortOrder: 3 },
  { code: 'ERP_PURCHASE_SUPPLY', name: '有償/無償支給', path: '/erp/purchase/material-supply', parentCode: 'ERP_PURCHASE', sortOrder: 4 },
  { code: 'ERP_PURCHASE_SUB_INV', name: '外注先在庫', path: '/erp/purchase/subcontract-inventory', parentCode: 'ERP_PURCHASE', sortOrder: 5 },
  { code: 'ERP_PURCHASE_ARRIVAL', name: '入荷予定管理', path: '/erp/purchase/arrival', parentCode: 'ERP_PURCHASE', sortOrder: 6 },
  { code: 'ERP_PURCHASE_RECEIPT', name: '受入登録', path: '/erp/purchase/receipt', parentCode: 'ERP_PURCHASE', sortOrder: 7 },
  { code: 'ERP_PURCHASE_INSPECTION', name: '受入検査', path: '/erp/purchase/inspection', parentCode: 'ERP_PURCHASE', sortOrder: 8 },
  { code: 'ERP_PURCHASE_INVOICE', name: '請求書照合', path: '/erp/purchase/invoice-matching', parentCode: 'ERP_PURCHASE', sortOrder: 9 },
  { code: 'ERP_PURCHASE_PAY_SCHEDULE', name: '支払予定表', path: '/erp/purchase/payment-schedule', parentCode: 'ERP_PURCHASE', sortOrder: 10 },
  { code: 'ERP_PURCHASE_BANK', name: 'FBデータ作成', path: '/erp/purchase/bank-transfer', parentCode: 'ERP_PURCHASE', sortOrder: 11 },

  // ===== 3. 在庫管理 (Inventory / WMS) =====
  { code: 'ERP_INVENTORY', name: '在庫管理', path: '/erp/inventory', icon: 'Box', parentCode: 'ERP', sortOrder: 5 },
  { code: 'ERP_INVENTORY_HOME', name: '在庫ホーム', path: '/erp/inventory', parentCode: 'ERP_INVENTORY', sortOrder: 0 },
  { code: 'ERP_INVENTORY_LIST', name: '在庫照会', path: '/erp/inventory/list', parentCode: 'ERP_INVENTORY', sortOrder: 1 },
  { code: 'ERP_INVENTORY_LOCATION', name: 'ロケーション管理', path: '/erp/inventory/location', parentCode: 'ERP_INVENTORY', sortOrder: 2 },
  { code: 'ERP_INVENTORY_TX', name: '入出庫履歴', path: '/erp/inventory/transactions', parentCode: 'ERP_INVENTORY', sortOrder: 3 },
  { code: 'ERP_INVENTORY_MOVEMENT', name: '入出庫移動', path: '/erp/inventory/movement', parentCode: 'ERP_INVENTORY', sortOrder: 4 },
  { code: 'ERP_INVENTORY_LOT', name: 'ロット・トレーサビリティ', path: '/erp/inventory/lot-trace', parentCode: 'ERP_INVENTORY', sortOrder: 5 },
  { code: 'ERP_INVENTORY_STOCKTAKING', name: '棚卸管理', path: '/erp/inventory/stocktaking', parentCode: 'ERP_INVENTORY', sortOrder: 6 },
  { code: 'ERP_INVENTORY_DEAD', name: '滞留在庫アラート', path: '/erp/inventory/dead-stock', parentCode: 'ERP_INVENTORY', sortOrder: 7 },
  { code: 'ERP_INVENTORY_ABC', name: 'ABC分析', path: '/erp/inventory/abc-analysis', parentCode: 'ERP_INVENTORY', sortOrder: 8 },
  { code: 'ERP_INVENTORY_STOCK_TX_LOG', name: '在庫取引記録', path: '/erp/inventory/stock-transaction-logs', parentCode: 'ERP_INVENTORY', sortOrder: 9 },

  // ===== 4. 生産管理 (Production Control / PP) =====
  { code: 'ERP_PRODUCTION', name: '生産管理', path: '/erp/production', icon: 'Setting', parentCode: 'ERP', sortOrder: 6 },
  { code: 'ERP_PRODUCTION_HOME', name: '生産ホーム', path: '/erp/production', parentCode: 'ERP_PRODUCTION', sortOrder: 0 },
  { code: 'ERP_PRODUCTION_ECO', name: '設計変更(ECO)', path: '/erp/production/eco', parentCode: 'ERP_PRODUCTION', sortOrder: 1 },
  { code: 'ERP_PRODUCTION_BOM', name: 'BOM展開', path: '/erp/production/bom', parentCode: 'ERP_PRODUCTION', sortOrder: 2 },
  { code: 'ERP_PRODUCTION_MRP', name: 'MRP（所要量計算）', path: '/erp/production/mrp', parentCode: 'ERP_PRODUCTION', sortOrder: 3 },
  { code: 'ERP_PRODUCTION_ORDERS', name: '生産オーダー', path: '/erp/production/orders', parentCode: 'ERP_PRODUCTION', sortOrder: 4 },
  { code: 'ERP_PRODUCTION_SERIAL', name: '製番管理', path: '/erp/production/serial', parentCode: 'ERP_PRODUCTION', sortOrder: 5 },
  { code: 'ERP_PRODUCTION_PLANNING', name: '生産計画', path: '/erp/production/data-management', parentCode: 'ERP_PRODUCTION', sortOrder: 5.5 },
  { code: 'ERP_PRODUCTION_DATA', name: '生産データ管理', path: '/erp/production/data-management', parentCode: 'ERP_PRODUCTION_PLANNING', sortOrder: 1 },
  { code: 'ERP_PRODUCTION_BASELINE', name: '計画ベースライン', path: '/erp/production/plan-baseline', parentCode: 'ERP_PRODUCTION_PLANNING', sortOrder: 2 },
  { code: 'ERP_PRODUCTION_INSTRUCTION', name: '生産指示', path: '/erp/production/instruction', parentCode: 'ERP_PRODUCTION', sortOrder: 5.6 },
  { code: 'ERP_PRODUCTION_INSTR_CUTTING', name: '切断指示', path: '/erp/production/instruction/cutting', parentCode: 'ERP_PRODUCTION_INSTRUCTION', sortOrder: 1 },
  { code: 'ERP_PRODUCTION_INSTR_SURFACE', name: '面取指示', path: '/erp/production/instruction/surface', parentCode: 'ERP_PRODUCTION_INSTRUCTION', sortOrder: 2 },
  { code: 'ERP_PRODUCTION_INSTR_FORMING', name: '成型指示', path: '/erp/production/instruction/forming', parentCode: 'ERP_PRODUCTION_INSTRUCTION', sortOrder: 3 },
  { code: 'ERP_PRODUCTION_INSTR_WELDING', name: '溶接指示', path: '/erp/production/instruction/welding', parentCode: 'ERP_PRODUCTION_INSTRUCTION', sortOrder: 4 },
  { code: 'ERP_PRODUCTION_INSTR_PLATING', name: 'メッキ指示', path: '/erp/production/instruction/plating', parentCode: 'ERP_PRODUCTION_INSTRUCTION', sortOrder: 5 },
  { code: 'ERP_PRODUCTION_WO', name: '製造指図書', path: '/erp/production/work-order', parentCode: 'ERP_PRODUCTION', sortOrder: 6 },
  { code: 'ERP_PRODUCTION_ISSUE', name: '材料出庫指示', path: '/erp/production/material-issue', parentCode: 'ERP_PRODUCTION', sortOrder: 7 },
  { code: 'ERP_PRODUCTION_RESULT', name: '生産実績', path: '/erp/production/actual-management', parentCode: 'ERP_PRODUCTION', sortOrder: 8 },
  { code: 'ERP_PRODUCTION_ACTUAL', name: '生産実績管理', path: '/erp/production/actual-management', parentCode: 'ERP_PRODUCTION_RESULT', sortOrder: 1 },
  { code: 'ERP_PRODUCTION_COMPLETE', name: '完成報告', path: '/erp/production/completion', parentCode: 'ERP_PRODUCTION_RESULT', sortOrder: 2 },
  { code: 'ERP_PRODUCTION_CONSUME', name: '材料消費実績', path: '/erp/production/consumption', parentCode: 'ERP_PRODUCTION_RESULT', sortOrder: 3 },

  // ===== 5. 原価・財務連携 (Costing & Finance) =====
  { code: 'ERP_COSTING', name: '原価・財務連携', path: '/erp/costing', icon: 'Coin', parentCode: 'ERP', sortOrder: 7 },
  { code: 'ERP_COSTING_HOME', name: '原価・会計ホーム', path: '/erp/costing', parentCode: 'ERP_COSTING', sortOrder: 0 },
  { code: 'ERP_COSTING_STANDARD', name: '標準原価計算', path: '/erp/costing/standard', parentCode: 'ERP_COSTING', sortOrder: 1 },
  { code: 'ERP_COSTING_ACTUAL', name: '実際原価計算', path: '/erp/costing/actual', parentCode: 'ERP_COSTING', sortOrder: 2 },
  { code: 'ERP_COSTING_VARIANCE', name: '原価差異分析', path: '/erp/costing/variance', parentCode: 'ERP_COSTING', sortOrder: 3 },
  { code: 'ERP_COSTING_ALLOCATION', name: '配賦計算', path: '/erp/costing/allocation', parentCode: 'ERP_COSTING', sortOrder: 4 },
  { code: 'ERP_COSTING_WIP', name: '仕掛品(WIP)評価', path: '/erp/costing/wip', parentCode: 'ERP_COSTING', sortOrder: 5 },
  { code: 'ERP_COSTING_EQUIPMENT', name: '設備台帳', path: '/erp/costing/equipment', parentCode: 'ERP_COSTING', sortOrder: 6 },
  { code: 'ERP_COSTING_DEPRECIATION', name: '減価償却計算', path: '/erp/costing/depreciation', parentCode: 'ERP_COSTING', sortOrder: 7 },
  { code: 'ERP_COSTING_JOURNAL', name: '自動仕訳生成', path: '/erp/costing/journal', parentCode: 'ERP_COSTING', sortOrder: 8 },
  { code: 'ERP_COSTING_ACCT_EXPORT', name: '会計ソフト出力', path: '/erp/costing/accounting-export', parentCode: 'ERP_COSTING', sortOrder: 9 },
  { code: 'ERP_COSTING_BILLING', name: '請求管理(AR)', path: '/erp/costing/billing', parentCode: 'ERP_COSTING', sortOrder: 10 },
  { code: 'ERP_COSTING_PAYMENT', name: '支払管理(AP)', path: '/erp/costing/payment', parentCode: 'ERP_COSTING', sortOrder: 11 },

  // ===== 6. 出荷管理 (Shipping Management) =====
  { code: 'ERP_SHIPPING', name: '出荷管理', path: '/erp/shipping', icon: 'Van', parentCode: 'ERP', sortOrder: 8 },
  { code: 'ERP_SHIPPING_LIST', name: '出荷構成表管理', path: '/erp/shipping', parentCode: 'ERP_SHIPPING', sortOrder: 1 },
  { code: 'ERP_SHIPPING_REPORT', name: '出荷報告書管理', path: '/erp/shipping/report', parentCode: 'ERP_SHIPPING', sortOrder: 2 },
  { code: 'ERP_SHIPPING_OVERVIEW', name: '出荷予定表発行', path: '/erp/shipping/overview', parentCode: 'ERP_SHIPPING', sortOrder: 3 },
  { code: 'ERP_SHIPPING_CONFIRM', name: '出荷確認リスト', path: '/erp/shipping/confirm', parentCode: 'ERP_SHIPPING', sortOrder: 4 },
  { code: 'ERP_SHIPPING_WELDING', name: '溶接出荷管理', path: '/erp/shipping/welding', parentCode: 'ERP_SHIPPING', sortOrder: 5 },
  { code: 'ERP_SHIPPING_PICKING', name: 'ピッキング管理', path: '/erp/shipping/picking', parentCode: 'ERP_SHIPPING', sortOrder: 6 },

  { code: 'APS', name: '生産スケジューラ', icon: 'DataAnalysis', sortOrder: 2 },
  { code: 'APS_PLANNING', name: '生産計画', path: '/aps/planning', parentCode: 'APS', sortOrder: 1 },
  { code: 'APS_SCHEDULING', name: 'スケジューリング', path: '/aps/scheduling', parentCode: 'APS', sortOrder: 2 },
  { code: 'MES', name: '製造実行メニュー', icon: 'Monitor', sortOrder: 3 },
  { code: 'MES_EXECUTION', name: '製造実行', path: '/mes/execution', parentCode: 'MES', sortOrder: 1 },
  { code: 'MES_QUALITY', name: '品質管理', path: '/mes/quality', parentCode: 'MES', sortOrder: 2 },
  { code: 'MASTER', name: 'マスタ管理', icon: 'Collection', sortOrder: 4 },
  { code: 'MASTER_LIST', name: 'マスタ', parentCode: 'MASTER', sortOrder: 1 },
  { code: 'MASTER_HOME', name: 'マスタホーム', path: '/master', parentCode: 'MASTER_LIST', sortOrder: 0 },
  { code: 'MASTER_PRODUCT', name: '製品マスタ', path: '/master/product', parentCode: 'MASTER_LIST', sortOrder: 1 },
  { code: 'MASTER_MATERIAL', name: '材料マスタ', path: '/master/material', parentCode: 'MASTER_LIST', sortOrder: 2 },
  { code: 'MASTER_SUPPLIER', name: '仕入先マスタ', path: '/master/supplier', parentCode: 'MASTER_LIST', sortOrder: 3 },
  { code: 'MASTER_PROCESS', name: '工程マスタ', path: '/master/process', parentCode: 'MASTER_LIST', sortOrder: 4 },
  { code: 'MASTER_PROCESS_ROUTE', name: '工程ルートマスタ', path: '/master/process-route', parentCode: 'MASTER_LIST', sortOrder: 5 },
  { code: 'MASTER_PRODUCT_PROCESS_ROUTE', name: '製品別工程ルートマスタ', path: '/master/product-process-route', parentCode: 'MASTER_LIST', sortOrder: 6 },
  { code: 'MASTER_CUSTOMER', name: '顧客マスタ', path: '/master/customer', parentCode: 'MASTER_LIST', sortOrder: 7 },
  { code: 'MASTER_CARRIER', name: '運送便マスタ', path: '/master/carrier', parentCode: 'MASTER_LIST', sortOrder: 8 },
  { code: 'MASTER_MACHINE', name: '設備マスタ', path: '/master/machine', parentCode: 'MASTER_LIST', sortOrder: 9 },
  { code: 'MASTER_DESTINATION', name: '納入先マスタ', path: '/master/destination', parentCode: 'MASTER_LIST', sortOrder: 10 },
  { code: 'MASTER_DESTINATION_HOLIDAY', name: '納入先休日設定', path: '/master/destination/holiday', parentCode: 'MASTER_LIST', sortOrder: 11 },
  { code: 'MASTER_BOM', name: 'BOM', parentCode: 'MASTER', sortOrder: 2 },
  { code: 'MASTER_BOM_HOME', name: 'BOMホーム', path: '/master/bom', parentCode: 'MASTER_BOM', sortOrder: 0 },
  { code: 'MASTER_PRODUCT_PROCESS_BOM', name: '製品工程BOM', path: '/master/bom/product-process', parentCode: 'MASTER_BOM', sortOrder: 1 },
  { code: 'MASTER_PRODUCT_MACHINE_CONFIG', name: '製品機器設定', path: '/master/bom/product-machine-config', parentCode: 'MASTER_BOM', sortOrder: 2 },
  { code: 'MASTER_EQUIPMENT_EFFICIENCY', name: '設備能率管理', path: '/master/bom/equipment-efficiency', parentCode: 'MASTER_BOM', sortOrder: 3 },
  { code: 'SYSTEM', name: 'システム管理', icon: 'Setting', sortOrder: 5 },
  { code: 'SYSTEM_USER', name: 'ユーザー・組織', icon: 'User', parentCode: 'SYSTEM', sortOrder: 1 },
  { code: 'SYSTEM_HOME', name: 'システムホーム', path: '/system', parentCode: 'SYSTEM_USER', sortOrder: 0 },
  { code: 'SYSTEM_USERS', name: 'ユーザー管理', path: '/system/users', parentCode: 'SYSTEM_USER', sortOrder: 1 },
  { code: 'SYSTEM_ORG', name: '組織・部門管理', path: '/system/organization', parentCode: 'SYSTEM_USER', sortOrder: 2 },
  { code: 'SYSTEM_ROLE', name: '権限・ロール管理', path: '/system/roles', parentCode: 'SYSTEM_USER', sortOrder: 3 },
  { code: 'SYSTEM_SETTINGS', name: 'システム設定', icon: 'Tools', parentCode: 'SYSTEM', sortOrder: 2 },
  { code: 'SYSTEM_NUMBERING', name: '採番ルール管理', path: '/system/numbering', parentCode: 'SYSTEM_SETTINGS', sortOrder: 1 },
  { code: 'SYSTEM_WORKFLOW', name: 'ワークフロー設定', path: '/system/workflow', parentCode: 'SYSTEM_SETTINGS', sortOrder: 2 },
  { code: 'SYSTEM_NOTIFICATION', name: '通知センター', path: '/system/notification', parentCode: 'SYSTEM_SETTINGS', sortOrder: 3 },
  { code: 'SYSTEM_LOGS', name: 'システムログ', path: '/system/logs', parentCode: 'SYSTEM_SETTINGS', sortOrder: 4 },
  { code: 'SYSTEM_DATA', name: 'データ管理', path: '/system/data', parentCode: 'SYSTEM_SETTINGS', sortOrder: 5 },
  { code: 'SYSTEM_MENUS', name: 'メニュー管理', path: '/system/menus', parentCode: 'SYSTEM_SETTINGS', sortOrder: 6 },
  { code: 'SYSTEM_FILE_WATCHER', name: 'ファイル監視設定', path: '/system/file-watcher', parentCode: 'SYSTEM_SETTINGS', sortOrder: 7 },
]
