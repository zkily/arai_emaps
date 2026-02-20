import type { RouteRecordRaw } from 'vue-router'

/** ERP モジュールルート（README準拠の5大モジュール構成） */
export const erpRoutes: RouteRecordRaw[] = [
  {
    path: '/erp',
    name: 'ERP',
    meta: { title: 'ERP', requiresAuth: true },
    children: [
      // ╔══════════════════════════════════════════════════════════════╗
      // ║  1. 販売管理 (Sales / SD)                                    ║
      // ╚══════════════════════════════════════════════════════════════╝
      {
        path: 'erp/sales',
        name: 'Sales',
        component: () => import('@/views/erp/Sales.vue'),
        meta: { title: '販売管理', group: '販売管理', requiresAuth: true },
      },
      // ── 見積管理 ──
      {
        path: 'erp/sales/quotation',
        name: 'QuotationList',
        component: () => import('@/views/erp/sales/quotation/QuotationList.vue'),
        meta: { title: '見積管理', group: '販売管理 > 見積管理', requiresAuth: true },
      },
      // ── 受注管理 ──
      {
        path: 'erp/sales/orders',
        name: 'SalesOrderList',
        component: () => import('@/views/erp/sales/SalesOrderList.vue'),
        meta: { title: '受注一覧', group: '販売管理 > 受注管理', requiresAuth: true },
      },
      {
        path: 'erp/sales/edi-import',
        redirect: '/erp/order/monthly',
      },
      {
        path: 'erp/sales/forecast',
        name: 'ForecastManagement',
        component: () => import('@/views/erp/sales/order/ForecastManagement.vue'),
        meta: { title: '内示・フォーキャスト管理', group: '販売管理 > 受注管理', requiresAuth: true },
      },
      {
        path: 'erp/sales/credit',
        name: 'CreditManagement',
        component: () => import('@/views/erp/sales/order/CreditManagement.vue'),
        meta: { title: '与信管理', group: '販売管理 > 受注管理', requiresAuth: true },
      },
      {
        path: 'erp/sales/contract-pricing',
        name: 'ContractPricing',
        component: () => import('@/views/erp/sales/order/ContractPricing.vue'),
        meta: { title: '契約単価管理', group: '販売管理 > 受注管理', requiresAuth: true },
      },
      // ── 出荷管理 ──
      {
        path: 'erp/sales/shipping',
        name: 'ShippingList',
        component: () => import('@/views/erp/sales/shipping/ShippingList.vue'),
        meta: { title: '出荷指示', group: '販売管理 > 出荷管理', requiresAuth: true },
      },
      // ── 売上・請求管理 ──
      {
        path: 'erp/sales/recording',
        name: 'SalesRecording',
        component: () => import('@/views/erp/sales/shipping/SalesRecording.vue'),
        meta: { title: '売上計上', group: '販売管理 > 売上・請求管理', requiresAuth: true },
      },
      {
        path: 'erp/sales/invoice',
        name: 'InvoiceIssue',
        component: () => import('@/views/erp/sales/billing/InvoiceIssue.vue'),
        meta: { title: '請求書発行', group: '販売管理 > 売上・請求管理', requiresAuth: true },
      },
      {
        path: 'erp/sales/return-correction',
        name: 'ReturnCorrection',
        component: () => import('@/views/erp/sales/billing/ReturnCorrection.vue'),
        meta: { title: '赤黒訂正処理', group: '販売管理 > 売上・請求管理', requiresAuth: true },
      },
      // ── 返品管理（既存互換） ──
      {
        path: 'erp/sales/returns',
        name: 'ReturnsList',
        component: () => import('@/views/erp/sales/returns/ReturnsList.vue'),
        meta: { title: '返品管理(RMA)', group: '販売管理', requiresAuth: true },
      },

      // ╔══════════════════════════════════════════════════════════════╗
      // ║  受注管理 (Order Management)                                  ║
      // ╚══════════════════════════════════════════════════════════════╝
      {
        path: 'erp/order',
        name: 'Order',
        component: () => import('@/views/erp/Order.vue'),
        meta: { title: '受注管理', group: '受注管理', requiresAuth: true },
      },
      {
        path: 'erp/order/monthly',
        name: 'OrderMonthlyList',
        component: () => import('@/views/erp/order/OrderMonthlyList.vue'),
        meta: { title: '月受注管理', group: '受注管理 > 月受注管理', requiresAuth: true },
      },
      {
        path: 'erp/order/daily',
        name: 'OrderDailyList',
        component: () => import('@/views/erp/order/OrderDailyList.vue'),
        meta: { title: '日受注管理', group: '受注管理 > 日受注管理', requiresAuth: true },
      },

      // ╔══════════════════════════════════════════════════════════════╗
      // ║  2. 購買・外注管理 (Procurement & Subcontracting)             ║
      // ╚══════════════════════════════════════════════════════════════╝
      {
        path: 'erp/purchase',
        name: 'Purchase',
        component: () => import('@/views/erp/Purchase.vue'),
        meta: { title: '購買・外注管理', group: '購買・外注管理', requiresAuth: true },
      },
      {
        path: 'erp/purchase/outsourcing',
        name: 'OutsourcingHome',
        component: () => import('@/views/erp/purchase/outsourcing/OutsourcingHome.vue'),
        meta: { title: '外注管理', group: 'メインメニュー', requiresAuth: true },
        children: [
          { path: '', redirect: { name: 'OutsourcingDashboard' } },
          { path: 'dashboard', name: 'OutsourcingDashboard', component: () => import('@/views/erp/purchase/outsourcing/dashboard/DashboardPage.vue'), meta: { title: '外注ダッシュボード', group: '外注管理', requiresAuth: true } },
          { path: 'plating-order', name: 'OutsourcingPlatingOrder', component: () => import('@/views/erp/purchase/outsourcing/plating/PlatingOrderPage.vue'), meta: { title: '外注メッキ注文', group: '注文管理', requiresAuth: true } },
          { path: 'plating-receiving', name: 'OutsourcingPlatingReceiving', component: () => import('@/views/erp/purchase/outsourcing/plating/PlatingReceivingPage.vue'), meta: { title: '外注メッキ受入', group: '受入管理', requiresAuth: true } },
          { path: 'welding-order', name: 'OutsourcingWeldingOrder', component: () => import('@/views/erp/purchase/outsourcing/welding/WeldingOrderPage.vue'), meta: { title: '外注溶接注文', group: '注文管理', requiresAuth: true } },
          { path: 'welding-receiving', name: 'OutsourcingWeldingReceiving', component: () => import('@/views/erp/purchase/outsourcing/welding/WeldingReceivingPage.vue'), meta: { title: '外注溶接受入', group: '受入管理', requiresAuth: true } },
          { path: 'suppliers', name: 'OutsourcingSuppliers', component: () => import('@/views/erp/purchase/outsourcing/suppliers/SuppliersPage.vue'), meta: { title: '外注先マスタ', group: 'マスタ', requiresAuth: true } },
          { path: 'stock', name: 'OutsourcingStock', component: () => import('@/views/erp/purchase/outsourcing/stock/OutsourcingStockPage.vue'), meta: { title: '外注在庫管理', group: '在庫管理', requiresAuth: true } },
          { path: 'supplied-material-stock', name: 'OutsourcingSuppliedMaterialStock', component: () => import('@/views/erp/purchase/outsourcing/material/SuppliedMaterialStockPage.vue'), meta: { title: '支給材料在庫', group: '支給材料管理', requiresAuth: true } },
          { path: 'usage', name: 'OutsourcingUsageManagement', component: () => import('@/views/erp/purchase/outsourcing/material/UsageManagementPage.vue'), meta: { title: '使用数管理', group: '支給材料管理', requiresAuth: true } },
          { path: 'material-issue', name: 'OutsourcingMaterialIssue', component: () => import('@/views/erp/purchase/outsourcing/material/MaterialIssuePage.vue'), meta: { title: '支給材料出庫', group: '支給材料管理', requiresAuth: true } },
        ],
      },

      // ╔══════════════════════════════════════════════════════════════╗
      // ║  3. 在庫管理 (Inventory / WMS)                               ║
      // ╚══════════════════════════════════════════════════════════════╝
      {
        path: 'erp/inventory',
        name: 'Inventory',
        component: () => import('@/views/erp/Inventory.vue'),
        meta: { title: '在庫管理', group: '在庫管理', requiresAuth: true },
      },
      // ── 在庫・ロケーション管理 ──
      {
        path: 'erp/inventory/list',
        name: 'InventoryList',
        component: () => import('@/views/erp/inventory/Inventory/InventoryList.vue'),
        meta: { title: '在庫照会', group: '在庫管理 > 在庫・ロケーション管理', requiresAuth: true },
      },
      {
        path: 'erp/inventory/stock-entry',
        name: 'StockEntryManagement',
        component: () => import('@/views/erp/inventory/stockEntry/UnifiedStockEntry.vue'),
        meta: { title: '在庫登録管理', group: '在庫管理 > 在庫・ロケーション管理', requiresAuth: true },
      },
      // ── 棚卸管理 ──
      {
        path: 'erp/inventory/stock-transaction-logs',
        name: 'StockTransactionLog',
        component: () => import('@/views/erp/inventory/stock/StockTransactionLog.vue'),
        meta: { title: '在庫取引記録', group: '在庫管理 > 入出庫・移動管理', requiresAuth: true },
      },

      // ╔══════════════════════════════════════════════════════════════╗
      // ║  4. 生産管理 (Production Control / PP)                       ║
      // ╚══════════════════════════════════════════════════════════════╝
      {
        path: 'erp/production',
        name: 'Production',
        component: () => import('@/views/erp/Production.vue'),
        meta: { title: '生産管理', group: '生産管理', requiresAuth: true },
      },
      // ── 生産計画 (ERP側) ──
      {
        path: 'erp/production/data-management',
        name: 'ProductionDataManagement',
        component: () => import('@/views/erp/production/planning/ProductionDataManagement.vue'),
        meta: { title: '生産データ管理', group: '生産管理 > 生産計画', requiresAuth: true },
      },
      {
        path: 'erp/production/plan-baseline',
        name: 'ProductionPlanBaselineManagement',
        component: () => import('@/views/erp/production/planning/ProductionPlanBaselineManagement.vue'),
        meta: { title: '生産計画ベースライン管理', group: '生産管理 > 生産計画', requiresAuth: true },
      },
      // ── 生産指示 ──
      {
        path: 'erp/production/instruction/cutting',
        name: 'CuttingInstruction',
        component: () => import('@/views/erp/production/instruction/cutting/CuttingInstruction.vue'),
        meta: { title: '切断指示', group: '生産管理 > 生産指示', requiresAuth: true },
      },
      {
        path: 'erp/production/instruction/surface',
        name: 'SurfaceInstruction',
        component: () => import('@/views/erp/production/instruction/surface/SurfaceInstruction.vue'),
        meta: { title: '面取指示', group: '生産管理 > 生産指示', requiresAuth: true },
      },
      {
        path: 'erp/production/instruction/forming',
        name: 'FormingInstruction',
        component: () => import('@/views/erp/production/instruction/forming/FormingInstruction.vue'),
        meta: { title: '成型指示', group: '生産管理 > 生産指示', requiresAuth: true },
      },
      {
        path: 'erp/production/instruction/welding',
        name: 'WeldingInstruction',
        component: () => import('@/views/erp/production/instruction/welding/WeldingInstruction.vue'),
        meta: { title: '溶接指示', group: '生産管理 > 生産指示', requiresAuth: true },
      },
      {
        path: 'erp/production/instruction/plating',
        name: 'PlatingInstruction',
        component: () => import('@/views/erp/production/instruction/plating/PlatingInstruction.vue'),
        meta: { title: 'メッキ指示', group: '生産管理 > 生産指示', requiresAuth: true },
      },
      // ── 生産実績 (ERP側) ──
      {
        path: 'erp/production/actual-management',
        name: 'ProductionActualManagement',
        component: () => import('@/views/erp/production/actual/ProductionActualManagement.vue'),
        meta: { title: '生産実績管理', group: '生産管理 > 生産実績', requiresAuth: true },
      },
      {
        path: 'erp/production/completion',
        name: 'CompletionReport',
        component: () => import('@/views/erp/production/actual/CompletionReport.vue'),
        meta: { title: '完成報告', group: '生産管理 > 生産実績', requiresAuth: true },
      },
      {
        path: 'erp/production/consumption',
        name: 'MaterialConsumption',
        component: () => import('@/views/erp/production/actual/MaterialConsumption.vue'),
        meta: { title: '材料消費実績', group: '生産管理 > 生産実績', requiresAuth: true },
      },

      // ╔══════════════════════════════════════════════════════════════╗
      // ║  5. 原価・財務連携 (Costing & Finance)                        ║
      // ╚══════════════════════════════════════════════════════════════╝
      {
        path: 'erp/costing',
        name: 'Costing',
        component: () => import('@/views/erp/Costing.vue'),
        meta: { title: '原価・会計', group: '原価・財務連携', requiresAuth: true },
      },
      // ── 原価計算 ──
      {
        path: 'erp/costing/standard',
        name: 'StandardCosting',
        component: () => import('@/views/erp/costing/cost/StandardCosting.vue'),
        meta: { title: '標準原価計算', group: '原価・財務連携 > 原価計算', requiresAuth: true },
      },
      {
        path: 'erp/costing/actual',
        name: 'ActualCosting',
        component: () => import('@/views/erp/costing/cost/ActualCosting.vue'),
        meta: { title: '実際原価計算', group: '原価・財務連携 > 原価計算', requiresAuth: true },
      },
      {
        path: 'erp/costing/variance',
        name: 'VarianceAnalysis',
        component: () => import('@/views/erp/costing/cost/VarianceAnalysis.vue'),
        meta: { title: '原価差異分析', group: '原価・財務連携 > 原価計算', requiresAuth: true },
      },
      {
        path: 'erp/costing/allocation',
        name: 'AllocationCalc',
        component: () => import('@/views/erp/costing/cost/AllocationCalc.vue'),
        meta: { title: '配賦計算', group: '原価・財務連携 > 原価計算', requiresAuth: true },
      },
      {
        path: 'erp/costing/wip',
        name: 'WipEvaluation',
        component: () => import('@/views/erp/costing/cost/WipEvaluation.vue'),
        meta: { title: '仕掛品(WIP)評価', group: '原価・財務連携 > 原価計算', requiresAuth: true },
      },
      // ── 固定資産管理 ──
      {
        path: 'erp/costing/equipment',
        name: 'EquipmentLedger',
        component: () => import('@/views/erp/costing/asset/EquipmentLedger.vue'),
        meta: { title: '設備台帳', group: '原価・財務連携 > 固定資産管理', requiresAuth: true },
      },
      {
        path: 'erp/costing/depreciation',
        name: 'Depreciation',
        component: () => import('@/views/erp/costing/asset/Depreciation.vue'),
        meta: { title: '減価償却計算', group: '原価・財務連携 > 固定資産管理', requiresAuth: true },
      },
      // ── 会計連携 ──
      {
        path: 'erp/costing/journal',
        name: 'JournalEntry',
        component: () => import('@/views/erp/costing/accounting/JournalEntry.vue'),
        meta: { title: '自動仕訳生成', group: '原価・財務連携 > 会計連携', requiresAuth: true },
      },
      {
        path: 'erp/costing/accounting-export',
        name: 'AccountingExport',
        component: () => import('@/views/erp/costing/accounting/AccountingExport.vue'),
        meta: { title: '会計ソフト出力', group: '原価・財務連携 > 会計連携', requiresAuth: true },
      },
      // ╔══════════════════════════════════════════════════════════════╗
      // ║  6. 出荷管理 (Shipping Management)                            ║
      // ╚══════════════════════════════════════════════════════════════╝
      {
        path: 'erp/shipping',
        name: 'ShippingHome',
        component: () => import('@/views/erp/shipping/ShippingHome.vue'),
        meta: { title: '出荷管理', group: '出荷管理', requiresAuth: true },
      },
      {
        path: 'erp/shipping/list',
        name: 'Shipping',
        component: () => import('@/views/erp/shipping/ShippingList.vue'),
        meta: { title: '出荷構成表管理', group: '出荷管理 > 出荷構成表管理', requiresAuth: true },
      },
      {
        path: 'erp/shipping/report',
        name: 'ShippingReport',
        component: () => import('@/views/erp/shipping/ShippingReportPage.vue'),
        meta: { title: '出荷報告書管理', group: '出荷管理 > 出荷報告書管理', requiresAuth: true },
      },
      {
        path: 'erp/shipping/overview',
        name: 'ShippingOverview',
        component: () => import('@/views/erp/shipping/ShippingOverview.vue'),
        meta: { title: '出荷予定表発行', group: '出荷管理 > 出荷予定表発行', requiresAuth: true },
      },
      {
        path: 'erp/shipping/confirm',
        name: 'ShippingListPage',
        component: () => import('@/views/erp/shipping/ShippingListPage.vue'),
        meta: { title: '出荷確認リスト', group: '出荷管理 > 出荷確認リスト', requiresAuth: true },
      },
      {
        path: 'erp/shipping/welding',
        name: 'WeldingShippingManager',
        component: () => import('@/views/erp/shipping/WeldingShippingManager.vue'),
        meta: { title: '溶接出荷管理', group: '出荷管理 > 溶接出荷管理', requiresAuth: true },
      },
      {
        path: 'erp/shipping/picking',
        name: 'ShippingPickingHome',
        component: () => import('@/views/erp/shipping/ShippingPickingHome.vue'),
        meta: { title: 'ピッキング管理', group: '出荷管理 > ピッキング管理', requiresAuth: true },
      },
      {
        path: 'erp/shipping/inventory-shortage',
        name: 'InventoryShortageManagement',
        component: () => import('@/views/erp/shipping/InventoryShortageManagement.vue'),
        meta: { title: '倉庫在庫管理', group: '出荷管理 > 倉庫在庫管理', requiresAuth: true },
      },
      {
        path: 'erp/shipping/abc-analysis',
        name: 'ShippingAbcAnalysis',
        component: () => import('@/views/erp/shipping/ShippingAbcAnalysis.vue'),
        meta: { title: 'ABC分析', group: '出荷管理 > ABC分析', requiresAuth: true },
      },
      {
        path: 'erp/shipping/inventory-kpi',
        name: 'InventoryKpi',
        component: () => import('@/views/erp/shipping/InventoryKpi.vue'),
        meta: { title: '在庫KPI・アラート', group: '出荷管理 > 在庫KPI', requiresAuth: true },
      },

      // ── 債権債務（既存互換） ──
      {
        path: 'erp/costing/billing',
        name: 'Billing',
        component: () => import('@/views/erp/costing/finance/Billing.vue'),
        meta: { title: '請求管理(AR)', group: '原価・財務連携 > 債権債務', requiresAuth: true },
      },
      {
        path: 'erp/costing/payment',
        name: 'Payment',
        component: () => import('@/views/erp/costing/finance/Payment.vue'),
        meta: { title: '支払管理(AP)', group: '原価・財務連携 > 債権債務', requiresAuth: true },
      },

    ],
  },
]
