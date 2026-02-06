import type { RouteRecordRaw } from 'vue-router'

/** ERP モジュールルート */
export const erpRoutes: RouteRecordRaw[] = [
  {
    path: '/erp',
    name: 'ERP',
    meta: { title: 'ERP', requiresAuth: true },
    children: [
      // ========== 販売管理 (Sales / SD) ==========
      {
        path: 'erp/sales',
        name: 'Sales',
        component: () => import('@/views/erp/Sales.vue'),
        meta: { title: '販売管理', group: '販売管理', requiresAuth: true },
      },
      // 見積・引合
      {
        path: 'erp/sales/quotation',
        name: 'QuotationList',
        component: () => import('@/views/erp/sales/quotation/QuotationList.vue'),
        meta: { title: '見積管理', group: '販売管理', requiresAuth: true },
      },
      // 受注プロセス
      {
        path: 'erp/sales/orders',
        name: 'SalesOrderList',
        component: () => import('@/views/erp/sales/SalesOrderList.vue'),
        meta: { title: '受注一覧', group: '販売管理', requiresAuth: true },
      },
      {
        path: 'erp/sales/edi-import',
        name: 'EdiImport',
        component: () => import('@/views/erp/sales/order/EdiImport.vue'),
        meta: { title: 'EDI取込', group: '販売管理', requiresAuth: true },
      },
      // 出荷・売上
      {
        path: 'erp/sales/shipping',
        name: 'ShippingList',
        component: () => import('@/views/erp/sales/shipping/ShippingList.vue'),
        meta: { title: '出荷指示', group: '販売管理', requiresAuth: true },
      },
      {
        path: 'erp/sales/recording',
        name: 'SalesRecording',
        component: () => import('@/views/erp/sales/shipping/SalesRecording.vue'),
        meta: { title: '売上計上', group: '販売管理', requiresAuth: true },
      },
      // 返品管理
      {
        path: 'erp/sales/returns',
        name: 'ReturnsList',
        component: () => import('@/views/erp/sales/returns/ReturnsList.vue'),
        meta: { title: '返品管理(RMA)', group: '販売管理', requiresAuth: true },
      },

      // ========== 購買管理 (Procurement / MM) ==========
      {
        path: 'erp/purchase',
        name: 'Purchase',
        component: () => import('@/views/erp/Purchase.vue'),
        meta: { title: '購買管理', group: '購買管理', requiresAuth: true },
      },
      // 発注プロセス
      {
        path: 'erp/purchase/orders',
        name: 'PurchaseOrderList',
        component: () => import('@/views/erp/purchase/PurchaseOrderList.vue'),
        meta: { title: '発注一覧', group: '購買管理', requiresAuth: true },
      },
      {
        path: 'erp/purchase/rfq',
        name: 'RfqList',
        component: () => import('@/views/erp/purchase/order/RfqList.vue'),
        meta: { title: '見積依頼(RFQ)', group: '購買管理', requiresAuth: true },
      },
      // 受入・在庫化
      {
        path: 'erp/purchase/arrival',
        name: 'ArrivalSchedule',
        component: () => import('@/views/erp/purchase/receiving/ArrivalSchedule.vue'),
        meta: { title: '入荷予定管理', group: '購買管理', requiresAuth: true },
      },
      {
        path: 'erp/purchase/receipt',
        name: 'ReceiptList',
        component: () => import('@/views/erp/purchase/receiving/ReceiptList.vue'),
        meta: { title: '受入登録', group: '購買管理', requiresAuth: true },
      },
      // 精算
      {
        path: 'erp/purchase/invoice-matching',
        name: 'InvoiceMatching',
        component: () => import('@/views/erp/purchase/settlement/InvoiceMatching.vue'),
        meta: { title: '請求書照合', group: '購買管理', requiresAuth: true },
      },

      // ========== 在庫管理 (Inventory / WMS) ==========
      {
        path: 'erp/inventory',
        name: 'Inventory',
        component: () => import('@/views/erp/Inventory.vue'),
        meta: { title: '在庫管理', group: '在庫管理', requiresAuth: true },
      },
      // 庫内オペレーション
      {
        path: 'erp/inventory/list',
        name: 'InventoryList',
        component: () => import('@/views/erp/inventory/InventoryList.vue'),
        meta: { title: '在庫照会', group: '在庫管理', requiresAuth: true },
      },
      {
        path: 'erp/inventory/transactions',
        name: 'InventoryTransactions',
        component: () => import('@/views/erp/inventory/InventoryTransactions.vue'),
        meta: { title: '入出庫履歴', group: '在庫管理', requiresAuth: true },
      },
      {
        path: 'erp/inventory/movement',
        name: 'StockMovement',
        component: () => import('@/views/erp/inventory/warehouse/StockMovement.vue'),
        meta: { title: '入出庫移動', group: '在庫管理', requiresAuth: true },
      },
      {
        path: 'erp/inventory/stocktaking',
        name: 'Stocktaking',
        component: () => import('@/views/erp/inventory/warehouse/Stocktaking.vue'),
        meta: { title: '棚卸管理', group: '在庫管理', requiresAuth: true },
      },
      // 在庫分析・最適化
      {
        path: 'erp/inventory/dead-stock',
        name: 'DeadStock',
        component: () => import('@/views/erp/inventory/analysis/DeadStock.vue'),
        meta: { title: '長期滞留在庫分析', group: '在庫分析', requiresAuth: true },
      },
      {
        path: 'erp/inventory/abc-analysis',
        name: 'AbcAnalysis',
        component: () => import('@/views/erp/inventory/analysis/AbcAnalysis.vue'),
        meta: { title: 'ABC分析', group: '在庫分析', requiresAuth: true },
      },

      // ========== 原価・会計連携 (Costing & Finance) ==========
      {
        path: 'erp/costing',
        name: 'Costing',
        component: () => import('@/views/erp/Costing.vue'),
        meta: { title: '原価・会計', group: '原価・会計', requiresAuth: true },
      },
      // 原価管理
      {
        path: 'erp/costing/standard',
        name: 'StandardCosting',
        component: () => import('@/views/erp/costing/cost/StandardCosting.vue'),
        meta: { title: '標準原価計算', group: '原価管理', requiresAuth: true },
      },
      {
        path: 'erp/costing/actual',
        name: 'ActualCosting',
        component: () => import('@/views/erp/costing/cost/ActualCosting.vue'),
        meta: { title: '実際原価計算', group: '原価管理', requiresAuth: true },
      },
      {
        path: 'erp/costing/variance',
        name: 'VarianceAnalysis',
        component: () => import('@/views/erp/costing/cost/VarianceAnalysis.vue'),
        meta: { title: '原価差異分析', group: '原価管理', requiresAuth: true },
      },
      // 債権債務
      {
        path: 'erp/costing/billing',
        name: 'Billing',
        component: () => import('@/views/erp/costing/finance/Billing.vue'),
        meta: { title: '請求管理(AR)', group: '債権債務', requiresAuth: true },
      },
      {
        path: 'erp/costing/payment',
        name: 'Payment',
        component: () => import('@/views/erp/costing/finance/Payment.vue'),
        meta: { title: '支払管理(AP)', group: '債権債務', requiresAuth: true },
      },

      // ========== マスタ ==========
      {
        path: 'erp/supplier',
        name: 'SupplierList',
        component: () => import('@/views/erp/supplier/SupplierList.vue'),
        meta: { title: '仕入先管理', group: 'マスタ', requiresAuth: true },
      },

      // ========== 受注管理モジュール（既存） ==========
      {
        path: 'erp/order',
        name: 'OrderHome',
        component: () => import('@/views/erp/order/OrderHome.vue'),
        meta: { title: '受注管理', group: '受注管理', requiresAuth: true },
      },
      {
        path: 'erp/order/monthly',
        name: 'OrderMonthlyList',
        component: () => import('@/views/erp/order/OrderMonthlyList.vue'),
        meta: { title: '月別受注管理', group: '受注管理', requiresAuth: true },
      },
      {
        path: 'erp/order/daily',
        name: 'OrderDailyList',
        component: () => import('@/views/erp/order/OrderDailyList.vue'),
        meta: { title: '日別受注管理', group: '受注管理', requiresAuth: true },
      },
      {
        path: 'erp/order/dashboard',
        name: 'OrderDashboardPage',
        component: () => import('@/views/erp/order/OrderDashboardPage.vue'),
        meta: { title: '受注ダッシュボード', group: '受注管理', requiresAuth: true },
      },
      {
        path: 'erp/order/kpi',
        name: 'OrderKpiDashboard',
        component: () => import('@/views/erp/order/OrderKpiDashboard.vue'),
        meta: { title: 'KPIダッシュボード', group: '受注管理', requiresAuth: true },
      },
      {
        path: 'erp/order/daily-history',
        name: 'OrderDailyHistoryPage',
        component: () => import('@/views/erp/order/OrderDailyHistoryPage.vue'),
        meta: { title: '日別受注履歴', group: '受注履歴', requiresAuth: true },
      },
      {
        path: 'erp/order/customer-history',
        name: 'OrderCustomerHistory',
        component: () => import('@/views/erp/order/OrderCustomerHistory.vue'),
        meta: { title: '顧客別受注履歴', group: '受注履歴', requiresAuth: true },
      },
      {
        path: 'erp/order/destination-history',
        name: 'OrderDestinationHistory',
        component: () => import('@/views/erp/order/OrderDestinationHistory.vue'),
        meta: { title: '納入先別受注履歴', group: '受注履歴', requiresAuth: true },
      },
      {
        path: 'erp/order/comparison',
        name: 'OrderHistoryComparison',
        component: () => import('@/views/erp/order/OrderHistoryComparison.vue'),
        meta: { title: '受注履歴比較', group: '受注履歴', requiresAuth: true },
      },
      {
        path: 'erp/order/print',
        name: 'OrderDailyPrintPage',
        component: () => import('@/views/erp/order/OrderDailyPrintPage.vue'),
        meta: { title: '受注印刷', group: '受注管理', requiresAuth: true },
      },
    ],
  },
]
