import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/modules/auth/stores/user'
import { getUserInfo } from '@/modules/auth/api'

const routes: RouteRecordRaw[] = [
  // ベースページ（layouts/pages で管理）
  {
    path: '/',
    name: 'Home',
    component: () => import('@/layouts/pages/Home.vue'),
    meta: { title: 'ホーム' },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/layouts/pages/Login.vue'),
    meta: { title: 'ログイン' },
  },
  {
    path: '/redirect/:path(.*)',
    name: 'Redirect',
    component: () => import('@/layouts/pages/Redirect.vue'),
    meta: { title: 'リダイレクト' },
  },
  // メインレイアウト配下のルート
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/layouts/pages/DashboardHome.vue'),
        meta: { title: 'ダッシュボード', requiresAuth: true },
      },
      // ========== ERP - 販売管理 (Sales / SD) ==========
      { path: 'erp/sales', name: 'Sales', component: () => import('@/views/erp/Sales.vue'), meta: { title: '販売管理', group: '販売管理', requiresAuth: true } },
      { path: 'erp/sales/quotation', name: 'QuotationList', component: () => import('@/views/erp/sales/quotation/QuotationList.vue'), meta: { title: '見積管理', group: '販売管理', requiresAuth: true } },
      { path: 'erp/sales/orders', name: 'SalesOrderList', component: () => import('@/views/erp/sales/SalesOrderList.vue'), meta: { title: '受注一覧', group: '販売管理', requiresAuth: true } },
      { path: 'erp/sales/edi-import', redirect: '/erp/order/monthly' },
      { path: 'erp/sales/shipping', name: 'ShippingList', component: () => import('@/views/erp/sales/shipping/ShippingList.vue'), meta: { title: '出荷指示', group: '販売管理', requiresAuth: true } },
      { path: 'erp/sales/recording', name: 'SalesRecording', component: () => import('@/views/erp/sales/shipping/SalesRecording.vue'), meta: { title: '売上計上', group: '販売管理', requiresAuth: true } },
      { path: 'erp/sales/returns', name: 'ReturnsList', component: () => import('@/views/erp/sales/returns/ReturnsList.vue'), meta: { title: '返品管理(RMA)', group: '販売管理', requiresAuth: true } },

      // ========== ERP - 受注管理 (Order Management) ==========
      { path: 'erp/order', name: 'Order', component: () => import('@/views/erp/Order.vue'), meta: { title: '受注管理', group: '受注管理', requiresAuth: true } },
      { path: 'erp/order/monthly', name: 'OrderMonthlyList', component: () => import('@/views/erp/order/OrderMonthlyList.vue'), meta: { title: '月受注管理', group: '受注管理 > 月受注管理', requiresAuth: true } },
      { path: 'erp/order/daily', name: 'OrderDailyList', component: () => import('@/views/erp/order/OrderDailyList.vue'), meta: { title: '日受注管理', group: '受注管理 > 日受注管理', requiresAuth: true } },

      // ========== ERP - 購買管理 (Procurement / MM) ==========
      { path: 'erp/purchase', name: 'Purchase', component: () => import('@/views/erp/Purchase.vue'), meta: { title: '購買管理', group: '購買管理', requiresAuth: true } },
      { path: 'erp/purchase/orders', name: 'PurchaseOrderList', component: () => import('@/views/erp/purchase/PurchaseOrderList.vue'), meta: { title: '発注一覧', group: '購買管理', requiresAuth: true } },
      { path: 'erp/purchase/rfq', name: 'RfqList', component: () => import('@/views/erp/purchase/order/RfqList.vue'), meta: { title: '見積依頼(RFQ)', group: '購買管理', requiresAuth: true } },
      { path: 'erp/purchase/arrival', name: 'ArrivalSchedule', component: () => import('@/views/erp/purchase/receiving/ArrivalSchedule.vue'), meta: { title: '入荷予定管理', group: '購買管理', requiresAuth: true } },
      { path: 'erp/purchase/receipt', name: 'ReceiptList', component: () => import('@/views/erp/purchase/receiving/ReceiptList.vue'), meta: { title: '受入登録', group: '購買管理', requiresAuth: true } },
      { path: 'erp/purchase/invoice-matching', name: 'InvoiceMatching', component: () => import('@/views/erp/purchase/settlement/InvoiceMatching.vue'), meta: { title: '請求書照合', group: '購買管理', requiresAuth: true } },

      // ========== ERP - 在庫管理 (Inventory / WMS) ==========
      { path: 'erp/inventory', name: 'Inventory', component: () => import('@/views/erp/Inventory.vue'), meta: { title: '在庫管理', group: '在庫管理', requiresAuth: true } },
      { path: 'erp/inventory/list', name: 'InventoryList', component: () => import('@/views/erp/inventory/InventoryList.vue'), meta: { title: '在庫照会', group: '在庫管理', requiresAuth: true } },
      { path: 'erp/inventory/transactions', name: 'InventoryTransactions', component: () => import('@/views/erp/inventory/InventoryTransactions.vue'), meta: { title: '入出庫履歴', group: '在庫管理', requiresAuth: true } },
      { path: 'erp/inventory/stock-transaction-logs', name: 'StockTransactionLog', component: () => import('@/views/erp/inventory/stock/StockTransactionLog.vue'), meta: { title: '在庫取引記録', group: '在庫管理', requiresAuth: true } },
      { path: 'erp/inventory/movement', name: 'StockMovement', component: () => import('@/views/erp/inventory/warehouse/StockMovement.vue'), meta: { title: '入出庫移動', group: '在庫管理', requiresAuth: true } },
      { path: 'erp/inventory/stocktaking', name: 'Stocktaking', component: () => import('@/views/erp/inventory/warehouse/Stocktaking.vue'), meta: { title: '棚卸管理', group: '在庫管理', requiresAuth: true } },
      { path: 'erp/inventory/dead-stock', name: 'DeadStock', component: () => import('@/views/erp/inventory/analysis/DeadStock.vue'), meta: { title: '長期滞留在庫分析', group: '在庫分析', requiresAuth: true } },
      { path: 'erp/inventory/abc-analysis', name: 'AbcAnalysis', component: () => import('@/views/erp/inventory/analysis/AbcAnalysis.vue'), meta: { title: 'ABC分析', group: '在庫分析', requiresAuth: true } },

      // ========== ERP - 生産管理 (Production Control / PP) ==========
      { path: 'erp/production', name: 'Production', component: () => import('@/views/erp/Production.vue'), meta: { title: '生産管理', group: '生産管理', requiresAuth: true } },
      { path: 'erp/production/eco', name: 'EcoManagement', component: () => import('@/views/erp/production/engineering/EcoManagement.vue'), meta: { title: '設計変更(ECO)管理', group: '生産管理 > エンジニアリング', requiresAuth: true } },
      { path: 'erp/production/bom', name: 'BomExplore', component: () => import('@/views/erp/production/engineering/BomExplore.vue'), meta: { title: 'BOM展開', group: '生産管理 > エンジニアリング', requiresAuth: true } },
      { path: 'erp/production/mrp', name: 'MrpCalculation', component: () => import('@/views/erp/production/planning/MrpCalculation.vue'), meta: { title: 'MRP（所要量計算）', group: '生産管理 > 生産計画', requiresAuth: true } },
      { path: 'erp/production/orders', name: 'ProductionOrder', component: () => import('@/views/erp/production/planning/ProductionOrder.vue'), meta: { title: '生産オーダー', group: '生産管理 > 生産計画', requiresAuth: true } },
      { path: 'erp/production/serial', name: 'SerialNumberManagement', component: () => import('@/views/erp/production/planning/SerialNumberManagement.vue'), meta: { title: '製番管理', group: '生産管理 > 生産計画', requiresAuth: true } },
      { path: 'erp/production/data-management', name: 'ProductionDataManagement', component: () => import('@/views/erp/production/planning/ProductionDataManagement.vue'), meta: { title: '生産データ管理', group: '生産管理 > 生産計画', requiresAuth: true } },
      { path: 'erp/production/plan-baseline', name: 'ProductionPlanBaselineManagement', component: () => import('@/views/erp/production/planning/ProductionPlanBaselineManagement.vue'), meta: { title: '生産計画ベースライン管理', group: '生産管理 > 生産計画', requiresAuth: true } },
      { path: 'erp/production/instruction/cutting', name: 'CuttingInstruction', component: () => import('@/views/erp/production/instruction/cutting/CuttingInstruction.vue'), meta: { title: '切断指示', group: '生産管理 > 生産指示', requiresAuth: true } },
      { path: 'erp/production/instruction/surface', name: 'SurfaceInstruction', component: () => import('@/views/erp/production/instruction/surface/SurfaceInstruction.vue'), meta: { title: '面取指示', group: '生産管理 > 生産指示', requiresAuth: true } },
      { path: 'erp/production/instruction/forming', name: 'FormingInstruction', component: () => import('@/views/erp/production/instruction/forming/FormingInstruction.vue'), meta: { title: '成型指示', group: '生産管理 > 生産指示', requiresAuth: true } },
      { path: 'erp/production/instruction/welding', name: 'WeldingInstruction', component: () => import('@/views/erp/production/instruction/welding/WeldingInstruction.vue'), meta: { title: '溶接指示', group: '生産管理 > 生産指示', requiresAuth: true } },
      { path: 'erp/production/instruction/plating', name: 'PlatingInstruction', component: () => import('@/views/erp/production/instruction/plating/PlatingInstruction.vue'), meta: { title: 'メッキ指示', group: '生産管理 > 生産指示', requiresAuth: true } },
      { path: 'erp/production/work-order', name: 'WorkOrder', component: () => import('@/views/erp/production/instruction/WorkOrder.vue'), meta: { title: '製造指図書', group: '生産管理 > 製造指示', requiresAuth: true } },
      { path: 'erp/production/material-issue', name: 'MaterialIssue', component: () => import('@/views/erp/production/instruction/MaterialIssue.vue'), meta: { title: '材料出庫指示', group: '生産管理 > 製造指示', requiresAuth: true } },
      { path: 'erp/production/actual-management', name: 'ProductionActualManagement', component: () => import('@/views/erp/production/actual/ProductionActualManagement.vue'), meta: { title: '生産実績管理', group: '生産管理 > 生産実績', requiresAuth: true } },
      { path: 'erp/production/completion', name: 'CompletionReport', component: () => import('@/views/erp/production/result/CompletionReport.vue'), meta: { title: '完成報告', group: '生産管理 > 生産実績', requiresAuth: true } },
      { path: 'erp/production/consumption', name: 'MaterialConsumption', component: () => import('@/views/erp/production/result/MaterialConsumption.vue'), meta: { title: '材料消費実績', group: '生産管理 > 生産実績', requiresAuth: true } },

      // ========== ERP - 原価・会計連携 (Costing & Finance) ==========
      { path: 'erp/costing', name: 'Costing', component: () => import('@/views/erp/Costing.vue'), meta: { title: '原価・会計', group: '原価・会計', requiresAuth: true } },
      { path: 'erp/costing/standard', name: 'StandardCosting', component: () => import('@/views/erp/costing/cost/StandardCosting.vue'), meta: { title: '標準原価計算', group: '原価管理', requiresAuth: true } },
      { path: 'erp/costing/actual', name: 'ActualCosting', component: () => import('@/views/erp/costing/cost/ActualCosting.vue'), meta: { title: '実際原価計算', group: '原価管理', requiresAuth: true } },
      { path: 'erp/costing/variance', name: 'VarianceAnalysis', component: () => import('@/views/erp/costing/cost/VarianceAnalysis.vue'), meta: { title: '原価差異分析', group: '原価管理', requiresAuth: true } },
      { path: 'erp/costing/billing', name: 'Billing', component: () => import('@/views/erp/costing/finance/Billing.vue'), meta: { title: '請求管理(AR)', group: '債権債務', requiresAuth: true } },
      { path: 'erp/costing/payment', name: 'Payment', component: () => import('@/views/erp/costing/finance/Payment.vue'), meta: { title: '支払管理(AP)', group: '債権債務', requiresAuth: true } },

      // ========== ERP - 出荷管理 (Shipping Management) ==========
      { path: 'erp/shipping', name: 'Shipping', component: () => import('@/views/erp/shipping/ShippingList.vue'), meta: { title: '出荷構成表管理', group: '出荷管理', requiresAuth: true } },
      { path: 'erp/shipping/report', name: 'ShippingReport', component: () => import('@/views/erp/shipping/ShippingReportPage.vue'), meta: { title: '出荷報告書管理', group: '出荷管理', requiresAuth: true } },
      { path: 'erp/shipping/overview', name: 'ShippingOverview', component: () => import('@/views/erp/shipping/ShippingOverview.vue'), meta: { title: '出荷予定表発行', group: '出荷管理', requiresAuth: true } },
      { path: 'erp/shipping/confirm', name: 'ShippingListPage', component: () => import('@/views/erp/shipping/ShippingListPage.vue'), meta: { title: '出荷確認リスト', group: '出荷管理', requiresAuth: true } },
      { path: 'erp/shipping/welding', name: 'WeldingShippingManager', component: () => import('@/views/erp/shipping/WeldingShippingManager.vue'), meta: { title: '溶接出荷管理', group: '出荷管理', requiresAuth: true } },
      { path: 'erp/shipping/picking', name: 'ShippingPickingHome', component: () => import('@/views/erp/shipping/ShippingPickingHome.vue'), meta: { title: 'ピッキング管理', group: '出荷管理', requiresAuth: true } },

      // ========== APS モジュール ==========
      { path: 'aps/planning', name: 'Planning', component: () => import('@/views/aps/Planning.vue'), meta: { title: '生産計画', requiresAuth: true } },
      { path: 'aps/scheduling', name: 'Scheduling', component: () => import('@/views/aps/Scheduling.vue'), meta: { title: 'スケジューリング', requiresAuth: true } },

      // ========== MES モジュール ==========
      { path: 'mes/execution', name: 'Execution', component: () => import('@/views/mes/Execution.vue'), meta: { title: '製造実行', requiresAuth: true } },
      { path: 'mes/quality', name: 'Quality', component: () => import('@/views/mes/Quality.vue'), meta: { title: '品質管理', requiresAuth: true } },

      // ========== マスタ管理 ==========
      { path: 'master', name: 'MasterHome', component: () => import('@/views/master/MasterList.vue'), meta: { title: 'マスタホーム', requiresAuth: true } },
      { path: 'master/product', name: 'ProductList', component: () => import('@/views/master/product/ProductList.vue'), meta: { title: '製品マスタ', requiresAuth: true } },
      { path: 'master/material', name: 'MaterialList', component: () => import('@/views/master/material/MaterialList.vue'), meta: { title: '材料マスタ', requiresAuth: true } },
      { path: 'master/supplier', name: 'SupplierList', component: () => import('@/views/master/supplier/SupplierList.vue'), meta: { title: '仕入先マスタ', requiresAuth: true } },
      { path: 'master/process', name: 'ProcessList', component: () => import('@/views/master/process/ProcessList.vue'), meta: { title: '工程マスタ', requiresAuth: true } },
      { path: 'master/process-route', name: 'ProcessRouteList', component: () => import('@/views/master/processRoute/ProcessRouteList.vue'), meta: { title: '工程ルートマスタ', requiresAuth: true } },
      { path: 'master/process-route/:route_cd/steps', name: 'RouteStepList', component: () => import('@/views/master/processRoute/ProcessRouteStepEditor.vue'), meta: { title: 'ルートステップ編集', requiresAuth: true } },
      { path: 'master/product-process-route', name: 'ProductProcessRouteManager', component: () => import('@/views/master/productProcessRoute/ProductRouteStepManager.vue'), meta: { title: '製品別工程ルートマスタ', requiresAuth: true } },
      { path: 'master/customer', name: 'CustomerList', component: () => import('@/views/master/customer/CustomerList.vue'), meta: { title: '顧客マスタ', requiresAuth: true } },
      { path: 'master/carrier', name: 'CarrierList', component: () => import('@/views/master/carrier/CarrierList.vue'), meta: { title: '運送便マスタ', requiresAuth: true } },
      { path: 'master/machine', name: 'MachineList', component: () => import('@/views/master/machine/MachineList.vue'), meta: { title: '設備マスタ', requiresAuth: true } },
      { path: 'master/destination', name: 'DestinationList', component: () => import('@/views/master/destination/DestinationList.vue'), meta: { title: '納入先マスタ', requiresAuth: true } },
      { path: 'master/destination/holiday', name: 'DestinationHoliday', component: () => import('@/views/master/destination/DestinationHoliday.vue'), meta: { title: '納入先休日設定', requiresAuth: true } },
      { path: 'master/bom', name: 'BomHome', component: () => import('@/views/master/BomList.vue'), meta: { title: 'BOMホーム', requiresAuth: true } },
      { path: 'master/bom/product-process', name: 'ProductProcessBOM', component: () => import('@/views/master/bom/ProductProcessBOM.vue'), meta: { title: '製品工程BOM', requiresAuth: true } },
      { path: 'master/bom/product-machine-config', name: 'ProductMachineConfig', component: () => import('@/views/master/bom/ProductMachineConfig.vue'), meta: { title: '製品機器設定', requiresAuth: true } },
      { path: 'master/bom/equipment-efficiency', name: 'EquipmentEfficiencyManagement', component: () => import('@/views/master/bom/EquipmentEfficiencyManagement.vue'), meta: { title: '設備能率管理', requiresAuth: true } },

      // ========== システム管理 (System Admin) ==========
      { path: 'system', name: 'System', component: () => import('@/views/system/SystemHome.vue'), meta: { title: 'システム管理', requiresAuth: true } },
      { path: 'system/users', name: 'UserList', component: () => import('@/views/system/user/UserList.vue'), meta: { title: 'ユーザー管理', requiresAuth: true } },
      { path: 'system/organization', name: 'OrganizationList', component: () => import('@/views/system/user/OrganizationList.vue'), meta: { title: '組織・部門管理', requiresAuth: true } },
      { path: 'system/roles', name: 'RolePermission', component: () => import('@/views/system/user/RolePermission.vue'), meta: { title: '権限・ロール管理', requiresAuth: true } },
      { path: 'system/numbering', name: 'NumberingRule', component: () => import('@/views/system/settings/NumberingRule.vue'), meta: { title: '採番ルール管理', requiresAuth: true } },
      { path: 'system/workflow', name: 'WorkflowSetting', component: () => import('@/views/system/settings/WorkflowSetting.vue'), meta: { title: 'ワークフロー設定', requiresAuth: true } },
      { path: 'system/notification', name: 'NotificationCenter', component: () => import('@/views/system/settings/NotificationCenter.vue'), meta: { title: '通知センター', requiresAuth: true } },
      { path: 'system/logs', name: 'SystemLog', component: () => import('@/views/system/settings/SystemLog.vue'), meta: { title: 'システムログ', requiresAuth: true } },
      { path: 'system/data', name: 'DataManagement', component: () => import('@/views/system/settings/DataManagement.vue'), meta: { title: 'データ管理', requiresAuth: true } },
      { path: 'system/menus', name: 'MenuManagement', component: () => import('@/views/system/settings/MenuManagement.vue'), meta: { title: 'メニュー管理', requiresAuth: true } },
      { path: 'system/file-watcher', name: 'FileWatcherSetting', component: () => import('@/views/system/settings/FileWatcherSetting.vue'), meta: { title: 'ファイル監視設定', requiresAuth: true } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ナビゲーションガード
router.beforeEach(async (to, from, next) => {
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - Smart-EMAP`
  }
  
  const userStore = useUserStore()
  
  // 認証チェック
  if (to.meta.requiresAuth) {
    if (!userStore.isAuthenticated) {
      // 未認証の場合はログインページにリダイレクト
      next({
        path: '/login',
        query: { redirect: to.fullPath }, // リダイレクト先を保存
      })
    } else {
      // 認証済みの場合、トークンの有効性を確認（単一デバイスログイン対応）
      try {
        await getUserInfo()
        // トークンが有効な場合、続行
        next()
      } catch (error: any) {
        // 他のデバイスでログインされた場合
        if (error?.response?.status === 401) {
          const errorDetail = error?.response?.data?.detail || ''
          const isForceLogout = error?.response?.headers?.['x-force-logout'] === 'true'
          const isOtherDeviceLogin = errorDetail.includes('他のデバイス') ||
                                     errorDetail.includes('他のデバイスでログイン') ||
                                     isForceLogout

          if (isOtherDeviceLogin) {
            const { ElMessage } = await import('element-plus')
            ElMessage.error({
              message: 'このアカウントは他のデバイスでログインされています。再度ログインしてください。',
              duration: 5000,
              showClose: true,
            })
          }
          userStore.clearLocalSession()
          next('/login')
          return
        }
        // その他のエラーは無視して続行
        next()
      }
    }
  } else {
    // ログインページにアクセスした場合、既にログインしている場合はダッシュボードにリダイレクト
    if ((to.path === '/login' || to.path === '/') && userStore.isAuthenticated) {
      // リダイレクト先がある場合はそこに、なければダッシュボードに
      const redirect = to.query.redirect as string
      next(redirect || '/dashboard')
    } else {
      next()
    }
  }
})

export default router
