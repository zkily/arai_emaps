<template>
  <div class="sidebar-menu">
    <!-- Logo -->
    <div class="logo" @click="goHome">
      <transition name="fade-text">
        <img v-if="!isCollapsed" src="/logo.png" alt="Smart-EMAP" class="logo-image" />
        <div v-else class="logo-icon-wrapper">
          <el-icon :size="22"><DataBoard /></el-icon>
        </div>
      </transition>
    </div>
    
    <!-- 菜单 -->
    <el-scrollbar class="menu-scrollbar">
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        :unique-opened="true"
        class="sidebar-el-menu"
        background-color="transparent"
        text-color="rgba(255, 255, 255, 0.75)"
        active-text-color="#ffffff"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title><span :title="t('menu.DASHBOARD')">{{ t('menu.DASHBOARD') }}</span></template>
        </el-menu-item>
        
        <el-sub-menu index="erp">
          <template #title>
            <el-icon><Management /></el-icon>
            <span :title="t('menu.ERP')">{{ t('menu.ERP') }}</span>
          </template>
          
          <el-sub-menu index="erp-sales">
            <template #title>
              <el-icon><Sell /></el-icon>
              <span :title="t('menu.ERP_SALES')">{{ t('menu.ERP_SALES') }}</span>
            </template>
            <el-menu-item index="/erp/sales"><el-icon><HomeFilled /></el-icon><template #title><span :title="t('menu.ERP_SALES_HOME')">{{ t('menu.ERP_SALES_HOME') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/sales/quotation"><el-icon><Document /></el-icon><template #title><span :title="t('menu.ERP_SALES_QUOTATION')">{{ t('menu.ERP_SALES_QUOTATION') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/sales/orders"><el-icon><List /></el-icon><template #title><span :title="t('menu.ERP_SALES_ORDERS')">{{ t('menu.ERP_SALES_ORDERS') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/sales/forecast"><el-icon><TrendCharts /></el-icon><template #title><span :title="t('menu.ERP_SALES_FORECAST')">{{ t('menu.ERP_SALES_FORECAST') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/sales/credit"><el-icon><CircleCheck /></el-icon><template #title><span :title="t('menu.ERP_SALES_CREDIT')">{{ t('menu.ERP_SALES_CREDIT') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/sales/contract-pricing"><el-icon><EditPen /></el-icon><template #title><span :title="t('menu.ERP_SALES_CONTRACT')">{{ t('menu.ERP_SALES_CONTRACT') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/sales/shipping"><el-icon><Van /></el-icon><template #title><span :title="t('menu.ERP_SALES_SHIPPING')">{{ t('menu.ERP_SALES_SHIPPING') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/sales/recording"><el-icon><DataLine /></el-icon><template #title><span :title="t('menu.ERP_SALES_RECORDING')">{{ t('menu.ERP_SALES_RECORDING') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/sales/invoice"><el-icon><Document /></el-icon><template #title><span :title="t('menu.ERP_SALES_INVOICE')">{{ t('menu.ERP_SALES_INVOICE') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/sales/return-correction"><el-icon><EditPen /></el-icon><template #title><span :title="t('menu.ERP_SALES_CORRECTION')">{{ t('menu.ERP_SALES_CORRECTION') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/sales/returns"><el-icon><Box /></el-icon><template #title><span :title="t('menu.ERP_SALES_RETURNS')">{{ t('menu.ERP_SALES_RETURNS') }}</span></template></el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="erp-purchase">
            <template #title>
              <el-icon><ShoppingCart /></el-icon>
              <span :title="t('menu.ERP_PURCHASE')">{{ t('menu.ERP_PURCHASE') }}</span>
            </template>
            <el-menu-item index="/erp/purchase"><el-icon><HomeFilled /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_HOME')">{{ t('menu.ERP_PURCHASE_HOME') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/orders"><el-icon><Document /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_ORDERS')">{{ t('menu.ERP_PURCHASE_ORDERS') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/rfq"><el-icon><List /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_RFQ')">{{ t('menu.ERP_PURCHASE_RFQ') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/subcontract-order"><el-icon><Connection /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_SUBCONTRACT')">{{ t('menu.ERP_PURCHASE_SUBCONTRACT') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/material-supply"><el-icon><Box /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_SUPPLY')">{{ t('menu.ERP_PURCHASE_SUPPLY') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/subcontract-inventory"><el-icon><Box /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_SUB_INV')">{{ t('menu.ERP_PURCHASE_SUB_INV') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/arrival"><el-icon><Van /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_ARRIVAL')">{{ t('menu.ERP_PURCHASE_ARRIVAL') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/receipt"><el-icon><CircleCheck /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_RECEIPT')">{{ t('menu.ERP_PURCHASE_RECEIPT') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/inspection"><el-icon><CircleCheck /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_INSPECTION')">{{ t('menu.ERP_PURCHASE_INSPECTION') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/invoice-matching"><el-icon><Document /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_INVOICE')">{{ t('menu.ERP_PURCHASE_INVOICE') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/payment-schedule"><el-icon><Calendar /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_PAY_SCHEDULE')">{{ t('menu.ERP_PURCHASE_PAY_SCHEDULE') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/purchase/bank-transfer"><el-icon><Coin /></el-icon><template #title><span :title="t('menu.ERP_PURCHASE_BANK')">{{ t('menu.ERP_PURCHASE_BANK') }}</span></template></el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="erp-order">
            <template #title>
              <el-icon><Document /></el-icon>
              <span :title="t('menu.ERP_ORDER')">{{ t('menu.ERP_ORDER') }}</span>
            </template>
            <el-menu-item index="/erp/order"><el-icon><HomeFilled /></el-icon><template #title><span :title="t('menu.ERP_ORDER_HOME')">{{ t('menu.ERP_ORDER_HOME') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/order/monthly"><el-icon><Calendar /></el-icon><template #title><span :title="t('menu.ERP_ORDER_MONTHLY')">{{ t('menu.ERP_ORDER_MONTHLY') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/order/daily"><el-icon><List /></el-icon><template #title><span :title="t('menu.ERP_ORDER_DAILY')">{{ t('menu.ERP_ORDER_DAILY') }}</span></template></el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="erp-inventory">
            <template #title>
              <el-icon><Box /></el-icon>
              <span :title="t('menu.ERP_INVENTORY')">{{ t('menu.ERP_INVENTORY') }}</span>
            </template>
            <el-menu-item index="/erp/inventory"><el-icon><HomeFilled /></el-icon><template #title><span :title="t('menu.ERP_INVENTORY_HOME')">{{ t('menu.ERP_INVENTORY_HOME') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/inventory/list"><el-icon><List /></el-icon><template #title><span :title="t('menu.ERP_INVENTORY_LIST')">{{ t('menu.ERP_INVENTORY_LIST') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/inventory/location"><el-icon><FolderOpened /></el-icon><template #title><span :title="t('menu.ERP_INVENTORY_LOCATION')">{{ t('menu.ERP_INVENTORY_LOCATION') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/inventory/transactions"><el-icon><DataLine /></el-icon><template #title><span :title="t('menu.ERP_INVENTORY_TX')">{{ t('menu.ERP_INVENTORY_TX') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/inventory/movement"><el-icon><Van /></el-icon><template #title><span :title="t('menu.ERP_INVENTORY_MOVEMENT')">{{ t('menu.ERP_INVENTORY_MOVEMENT') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/inventory/lot-trace"><el-icon><Connection /></el-icon><template #title><span :title="t('menu.ERP_INVENTORY_LOT')">{{ t('menu.ERP_INVENTORY_LOT') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/inventory/stocktaking"><el-icon><List /></el-icon><template #title><span :title="t('menu.ERP_INVENTORY_STOCKTAKING')">{{ t('menu.ERP_INVENTORY_STOCKTAKING') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/inventory/dead-stock"><el-icon><Box /></el-icon><template #title><span :title="t('menu.ERP_INVENTORY_DEAD')">{{ t('menu.ERP_INVENTORY_DEAD') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/inventory/abc-analysis"><el-icon><DataAnalysis /></el-icon><template #title><span :title="t('menu.ERP_INVENTORY_ABC')">{{ t('menu.ERP_INVENTORY_ABC') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/inventory/stock-transaction-logs"><el-icon><DataLine /></el-icon><template #title><span :title="t('menu.ERP_INVENTORY_STOCK_TX_LOG')">{{ t('menu.ERP_INVENTORY_STOCK_TX_LOG') }}</span></template></el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="erp-production">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span :title="t('menu.ERP_PRODUCTION')">{{ t('menu.ERP_PRODUCTION') }}</span>
            </template>
            <el-menu-item index="/erp/production">
              <el-icon><HomeFilled /></el-icon>
              <template #title><span :title="t('menu.ERP_PRODUCTION_HOME')">{{ t('menu.ERP_PRODUCTION_HOME') }}</span></template>
            </el-menu-item>
            <el-menu-item index="/erp/production/eco">
              <el-icon><EditPen /></el-icon>
              <template #title><span :title="t('menu.ERP_PRODUCTION_ECO')">{{ t('menu.ERP_PRODUCTION_ECO') }}</span></template>
            </el-menu-item>
            <el-menu-item index="/erp/production/bom">
              <el-icon><Connection /></el-icon>
              <template #title><span :title="t('menu.ERP_PRODUCTION_BOM')">{{ t('menu.ERP_PRODUCTION_BOM') }}</span></template>
            </el-menu-item>
            <el-menu-item index="/erp/production/mrp">
              <el-icon><DataAnalysis /></el-icon>
              <template #title><span :title="t('menu.ERP_PRODUCTION_MRP')">{{ t('menu.ERP_PRODUCTION_MRP') }}</span></template>
            </el-menu-item>
            <el-menu-item index="/erp/production/orders">
              <el-icon><Document /></el-icon>
              <template #title><span :title="t('menu.ERP_PRODUCTION_ORDERS')">{{ t('menu.ERP_PRODUCTION_ORDERS') }}</span></template>
            </el-menu-item>
            <el-menu-item index="/erp/production/serial">
              <el-icon><Tickets /></el-icon>
              <template #title><span :title="t('menu.ERP_PRODUCTION_SERIAL')">{{ t('menu.ERP_PRODUCTION_SERIAL') }}</span></template>
            </el-menu-item>
            <el-sub-menu index="erp-production-planning">
              <template #title>
                <el-icon><Calendar /></el-icon>
                <span :title="t('menu.ERP_PRODUCTION_PLANNING')">{{ t('menu.ERP_PRODUCTION_PLANNING') }}</span>
              </template>
              <el-menu-item index="/erp/production/data-management">
                <el-icon><DataLine /></el-icon>
                <template #title><span :title="t('menu.ERP_PRODUCTION_DATA')">{{ t('menu.ERP_PRODUCTION_DATA') }}</span></template>
              </el-menu-item>
              <el-menu-item index="/erp/production/plan-baseline">
                <el-icon><TrendCharts /></el-icon>
                <template #title><span :title="t('menu.ERP_PRODUCTION_BASELINE')">{{ t('menu.ERP_PRODUCTION_BASELINE') }}</span></template>
              </el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="erp-production-instruction">
              <template #title>
                <el-icon><Memo /></el-icon>
                <span :title="t('menu.ERP_PRODUCTION_INSTRUCTION')">{{ t('menu.ERP_PRODUCTION_INSTRUCTION') }}</span>
              </template>
              <el-menu-item index="/erp/production/instruction/cutting">
                <el-icon><Operation /></el-icon>
                <template #title><span :title="t('menu.ERP_PRODUCTION_INSTR_CUTTING')">{{ t('menu.ERP_PRODUCTION_INSTR_CUTTING') }}</span></template>
              </el-menu-item>
              <el-menu-item index="/erp/production/instruction/surface">
                <el-icon><Operation /></el-icon>
                <template #title><span :title="t('menu.ERP_PRODUCTION_INSTR_SURFACE')">{{ t('menu.ERP_PRODUCTION_INSTR_SURFACE') }}</span></template>
              </el-menu-item>
              <el-menu-item index="/erp/production/instruction/forming">
                <el-icon><Operation /></el-icon>
                <template #title><span :title="t('menu.ERP_PRODUCTION_INSTR_FORMING')">{{ t('menu.ERP_PRODUCTION_INSTR_FORMING') }}</span></template>
              </el-menu-item>
              <el-menu-item index="/erp/production/instruction/welding">
                <el-icon><Connection /></el-icon>
                <template #title><span :title="t('menu.ERP_PRODUCTION_INSTR_WELDING')">{{ t('menu.ERP_PRODUCTION_INSTR_WELDING') }}</span></template>
              </el-menu-item>
              <el-menu-item index="/erp/production/instruction/plating">
                <el-icon><Operation /></el-icon>
                <template #title><span :title="t('menu.ERP_PRODUCTION_INSTR_PLATING')">{{ t('menu.ERP_PRODUCTION_INSTR_PLATING') }}</span></template>
              </el-menu-item>
            </el-sub-menu>
            <el-menu-item index="/erp/production/work-order">
              <el-icon><Document /></el-icon>
              <template #title><span :title="t('menu.ERP_PRODUCTION_WO')">{{ t('menu.ERP_PRODUCTION_WO') }}</span></template>
            </el-menu-item>
            <el-menu-item index="/erp/production/material-issue">
              <el-icon><Box /></el-icon>
              <template #title><span :title="t('menu.ERP_PRODUCTION_ISSUE')">{{ t('menu.ERP_PRODUCTION_ISSUE') }}</span></template>
            </el-menu-item>
            <el-sub-menu index="erp-production-result">
              <template #title>
                <el-icon><DataLine /></el-icon>
                <span :title="t('menu.ERP_PRODUCTION_RESULT')">{{ t('menu.ERP_PRODUCTION_RESULT') }}</span>
              </template>
              <el-menu-item index="/erp/production/actual-management">
                <el-icon><TrendCharts /></el-icon>
                <template #title><span :title="t('menu.ERP_PRODUCTION_ACTUAL')">{{ t('menu.ERP_PRODUCTION_ACTUAL') }}</span></template>
              </el-menu-item>
              <el-menu-item index="/erp/production/completion">
                <el-icon><CircleCheck /></el-icon>
                <template #title><span :title="t('menu.ERP_PRODUCTION_COMPLETE')">{{ t('menu.ERP_PRODUCTION_COMPLETE') }}</span></template>
              </el-menu-item>
              <el-menu-item index="/erp/production/consumption">
                <el-icon><DataLine /></el-icon>
                <template #title><span :title="t('menu.ERP_PRODUCTION_CONSUME')">{{ t('menu.ERP_PRODUCTION_CONSUME') }}</span></template>
              </el-menu-item>
            </el-sub-menu>
          </el-sub-menu>
          
          <el-sub-menu index="erp-shipping">
            <template #title>
              <el-icon><Van /></el-icon>
              <span :title="t('menu.ERP_SHIPPING')">{{ t('menu.ERP_SHIPPING') }}</span>
            </template>
            <el-menu-item index="/erp/shipping"><el-icon><List /></el-icon><template #title><span :title="t('menu.ERP_SHIPPING_LIST')">{{ t('menu.ERP_SHIPPING_LIST') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/shipping/report"><el-icon><Document /></el-icon><template #title><span :title="t('menu.ERP_SHIPPING_REPORT')">{{ t('menu.ERP_SHIPPING_REPORT') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/shipping/overview"><el-icon><Calendar /></el-icon><template #title><span :title="t('menu.ERP_SHIPPING_OVERVIEW')">{{ t('menu.ERP_SHIPPING_OVERVIEW') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/shipping/confirm"><el-icon><CircleCheck /></el-icon><template #title><span :title="t('menu.ERP_SHIPPING_CONFIRM')">{{ t('menu.ERP_SHIPPING_CONFIRM') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/shipping/welding"><el-icon><Connection /></el-icon><template #title><span :title="t('menu.ERP_SHIPPING_WELDING')">{{ t('menu.ERP_SHIPPING_WELDING') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/shipping/picking"><el-icon><Box /></el-icon><template #title><span :title="t('menu.ERP_SHIPPING_PICKING')">{{ t('menu.ERP_SHIPPING_PICKING') }}</span></template></el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="erp-costing">
            <template #title>
              <el-icon><Coin /></el-icon>
              <span :title="t('menu.ERP_COSTING')">{{ t('menu.ERP_COSTING') }}</span>
            </template>
            <el-menu-item index="/erp/costing"><el-icon><HomeFilled /></el-icon><template #title><span :title="t('menu.ERP_COSTING_HOME')">{{ t('menu.ERP_COSTING_HOME') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/standard"><el-icon><Coin /></el-icon><template #title><span :title="t('menu.ERP_COSTING_STANDARD')">{{ t('menu.ERP_COSTING_STANDARD') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/actual"><el-icon><DataLine /></el-icon><template #title><span :title="t('menu.ERP_COSTING_ACTUAL')">{{ t('menu.ERP_COSTING_ACTUAL') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/variance"><el-icon><TrendCharts /></el-icon><template #title><span :title="t('menu.ERP_COSTING_VARIANCE')">{{ t('menu.ERP_COSTING_VARIANCE') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/allocation"><el-icon><DataAnalysis /></el-icon><template #title><span :title="t('menu.ERP_COSTING_ALLOCATION')">{{ t('menu.ERP_COSTING_ALLOCATION') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/wip"><el-icon><Box /></el-icon><template #title><span :title="t('menu.ERP_COSTING_WIP')">{{ t('menu.ERP_COSTING_WIP') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/equipment"><el-icon><Setting /></el-icon><template #title><span :title="t('menu.ERP_COSTING_EQUIPMENT')">{{ t('menu.ERP_COSTING_EQUIPMENT') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/depreciation"><el-icon><Calendar /></el-icon><template #title><span :title="t('menu.ERP_COSTING_DEPRECIATION')">{{ t('menu.ERP_COSTING_DEPRECIATION') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/journal"><el-icon><Document /></el-icon><template #title><span :title="t('menu.ERP_COSTING_JOURNAL')">{{ t('menu.ERP_COSTING_JOURNAL') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/accounting-export"><el-icon><Document /></el-icon><template #title><span :title="t('menu.ERP_COSTING_ACCT_EXPORT')">{{ t('menu.ERP_COSTING_ACCT_EXPORT') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/billing"><el-icon><Document /></el-icon><template #title><span :title="t('menu.ERP_COSTING_BILLING')">{{ t('menu.ERP_COSTING_BILLING') }}</span></template></el-menu-item>
            <el-menu-item index="/erp/costing/payment"><el-icon><Coin /></el-icon><template #title><span :title="t('menu.ERP_COSTING_PAYMENT')">{{ t('menu.ERP_COSTING_PAYMENT') }}</span></template></el-menu-item>
          </el-sub-menu>
        </el-sub-menu>
        
        <el-sub-menu index="aps">
          <template #title>
            <el-icon><DataAnalysis /></el-icon>
            <span :title="t('menu.APS')">{{ t('menu.APS') }}</span>
          </template>
          <el-menu-item index="/aps/planning">
            <el-icon><Calendar /></el-icon>
            <template #title><span :title="t('menu.APS_PLANNING')">{{ t('menu.APS_PLANNING') }}</span></template>
          </el-menu-item>
          <el-menu-item index="/aps/scheduling">
            <el-icon><Timer /></el-icon>
            <template #title><span :title="t('menu.APS_SCHEDULING')">{{ t('menu.APS_SCHEDULING') }}</span></template>
          </el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="mes">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span :title="t('menu.MES')">{{ t('menu.MES') }}</span>
          </template>
          <el-menu-item index="/mes/execution">
            <el-icon><VideoPlay /></el-icon>
            <template #title><span :title="t('menu.MES_EXECUTION')">{{ t('menu.MES_EXECUTION') }}</span></template>
          </el-menu-item>
          <el-menu-item index="/mes/quality">
            <el-icon><CircleCheck /></el-icon>
            <template #title><span :title="t('menu.MES_QUALITY')">{{ t('menu.MES_QUALITY') }}</span></template>
          </el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="master">
          <template #title>
            <el-icon><Collection /></el-icon>
            <span :title="t('menu.MASTER')">{{ t('menu.MASTER') }}</span>
          </template>
          <el-sub-menu index="master-list">
            <template #title>
              <el-icon><List /></el-icon>
              <span :title="t('menu.MASTER_LIST')">{{ t('menu.MASTER_LIST') }}</span>
            </template>
            <el-menu-item index="/master"><el-icon><HomeFilled /></el-icon><template #title><span :title="t('menu.MASTER_HOME')">{{ t('menu.MASTER_HOME') }}</span></template></el-menu-item>
            <el-menu-item index="/master/product"><el-icon><Box /></el-icon><template #title><span :title="t('menu.MASTER_PRODUCT')">{{ t('menu.MASTER_PRODUCT') }}</span></template></el-menu-item>
            <el-menu-item index="/master/material"><el-icon><Collection /></el-icon><template #title><span :title="t('menu.MASTER_MATERIAL')">{{ t('menu.MASTER_MATERIAL') }}</span></template></el-menu-item>
            <el-menu-item index="/master/customer"><el-icon><User /></el-icon><template #title><span :title="t('menu.MASTER_CUSTOMER')">{{ t('menu.MASTER_CUSTOMER') }}</span></template></el-menu-item>
            <el-menu-item index="/master/supplier"><el-icon><ShoppingCart /></el-icon><template #title><span :title="t('menu.MASTER_SUPPLIER')">{{ t('menu.MASTER_SUPPLIER') }}</span></template></el-menu-item>
            <el-menu-item index="/master/destination"><el-icon><FolderOpened /></el-icon><template #title><span :title="t('menu.MASTER_DESTINATION')">{{ t('menu.MASTER_DESTINATION') }}</span></template></el-menu-item>
            <el-menu-item index="/master/destination/holiday"><el-icon><Calendar /></el-icon><template #title><span :title="t('menu.MASTER_DESTINATION_HOLIDAY')">{{ t('menu.MASTER_DESTINATION_HOLIDAY') }}</span></template></el-menu-item>
            <el-menu-item index="/master/carrier"><el-icon><Van /></el-icon><template #title><span :title="t('menu.MASTER_CARRIER')">{{ t('menu.MASTER_CARRIER') }}</span></template></el-menu-item>
            <el-menu-item index="/master/machine"><el-icon><Setting /></el-icon><template #title><span :title="t('menu.MASTER_MACHINE')">{{ t('menu.MASTER_MACHINE') }}</span></template></el-menu-item>
            <el-menu-item index="/master/process"><el-icon><Operation /></el-icon><template #title><span :title="t('menu.MASTER_PROCESS')">{{ t('menu.MASTER_PROCESS') }}</span></template></el-menu-item>
            <el-menu-item index="/master/process-route"><el-icon><Connection /></el-icon><template #title><span :title="t('menu.MASTER_PROCESS_ROUTE')">{{ t('menu.MASTER_PROCESS_ROUTE') }}</span></template></el-menu-item>
            <el-menu-item index="/master/product-process-route"><el-icon><Connection /></el-icon><template #title><span :title="t('menu.MASTER_PRODUCT_PROCESS_ROUTE')">{{ t('menu.MASTER_PRODUCT_PROCESS_ROUTE') }}</span></template></el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="master-bom">
            <template #title>
              <el-icon><Connection /></el-icon>
              <span :title="t('menu.MASTER_BOM')">{{ t('menu.MASTER_BOM') }}</span>
            </template>
            <el-menu-item index="/master/bom"><el-icon><HomeFilled /></el-icon><template #title><span :title="t('menu.MASTER_BOM_HOME')">{{ t('menu.MASTER_BOM_HOME') }}</span></template></el-menu-item>
            <el-menu-item index="/master/bom/product-process"><el-icon><Connection /></el-icon><template #title><span :title="t('menu.MASTER_PRODUCT_PROCESS_BOM')">{{ t('menu.MASTER_PRODUCT_PROCESS_BOM') }}</span></template></el-menu-item>
            <el-menu-item index="/master/bom/product-machine-config"><el-icon><Setting /></el-icon><template #title><span :title="t('menu.MASTER_PRODUCT_MACHINE_CONFIG')">{{ t('menu.MASTER_PRODUCT_MACHINE_CONFIG') }}</span></template></el-menu-item>
            <el-menu-item index="/master/bom/equipment-efficiency"><el-icon><TrendCharts /></el-icon><template #title><span :title="t('menu.MASTER_EQUIPMENT_EFFICIENCY')">{{ t('menu.MASTER_EQUIPMENT_EFFICIENCY') }}</span></template></el-menu-item>
          </el-sub-menu>
        </el-sub-menu>
        
        <el-sub-menu v-if="userStore.hasPermission('all')" index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span :title="t('menu.SYSTEM')">{{ t('menu.SYSTEM') }}</span>
          </template>
          
          <el-sub-menu index="system-user">
            <template #title>
              <el-icon><User /></el-icon>
              <span :title="t('menu.SYSTEM_USER')">{{ t('menu.SYSTEM_USER') }}</span>
            </template>
            <el-menu-item index="/system"><el-icon><HomeFilled /></el-icon><template #title><span :title="t('menu.SYSTEM_HOME')">{{ t('menu.SYSTEM_HOME') }}</span></template></el-menu-item>
            <el-menu-item index="/system/users"><el-icon><User /></el-icon><template #title><span :title="t('menu.SYSTEM_USERS')">{{ t('menu.SYSTEM_USERS') }}</span></template></el-menu-item>
            <el-menu-item index="/system/organization"><el-icon><Connection /></el-icon><template #title><span :title="t('menu.SYSTEM_ORG')">{{ t('menu.SYSTEM_ORG') }}</span></template></el-menu-item>
            <el-menu-item index="/system/roles"><el-icon><List /></el-icon><template #title><span :title="t('menu.SYSTEM_ROLE')">{{ t('menu.SYSTEM_ROLE') }}</span></template></el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="system-settings">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span :title="t('menu.SYSTEM_SETTINGS')">{{ t('menu.SYSTEM_SETTINGS') }}</span>
            </template>
            <el-menu-item index="/system/numbering"><el-icon><Tickets /></el-icon><template #title><span :title="t('menu.SYSTEM_NUMBERING')">{{ t('menu.SYSTEM_NUMBERING') }}</span></template></el-menu-item>
            <el-menu-item index="/system/workflow"><el-icon><Connection /></el-icon><template #title><span :title="t('menu.SYSTEM_WORKFLOW')">{{ t('menu.SYSTEM_WORKFLOW') }}</span></template></el-menu-item>
            <el-menu-item index="/system/notification"><el-icon><CircleCheck /></el-icon><template #title><span :title="t('menu.SYSTEM_NOTIFICATION')">{{ t('menu.SYSTEM_NOTIFICATION') }}</span></template></el-menu-item>
            <el-menu-item index="/system/logs"><el-icon><Document /></el-icon><template #title><span :title="t('menu.SYSTEM_LOGS')">{{ t('menu.SYSTEM_LOGS') }}</span></template></el-menu-item>
            <el-menu-item index="/system/data"><el-icon><DataLine /></el-icon><template #title><span :title="t('menu.SYSTEM_DATA')">{{ t('menu.SYSTEM_DATA') }}</span></template></el-menu-item>
            <el-menu-item index="/system/menus"><el-icon><List /></el-icon><template #title><span :title="t('menu.SYSTEM_MENUS')">{{ t('menu.SYSTEM_MENUS') }}</span></template></el-menu-item>
            <el-menu-item index="/system/file-watcher"><el-icon><Monitor /></el-icon><template #title><span :title="t('menu.SYSTEM_FILE_WATCHER')">{{ t('menu.SYSTEM_FILE_WATCHER') }}</span></template></el-menu-item>
          </el-sub-menu>
        </el-sub-menu>
      </el-menu>
    </el-scrollbar>
    
    <!-- 折叠按钮 -->
    <div class="collapse-btn" @click="toggleCollapse">
      <el-icon :size="16">
        <component :is="isCollapsed ? 'Expand' : 'Fold'" />
      </el-icon>
      <transition name="fade-text">
        <span v-if="!isCollapsed" class="collapse-text">{{ t('menu.COLLAPSE') || '收起' }}</span>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/modules/auth/stores/user'
import {
  HomeFilled, Management, Sell, ShoppingCart, Box, Coin, Document,
  User, DataAnalysis, Monitor, DataBoard, Setting, Tools,
  Collection, List, Connection, Calendar, Timer, VideoPlay, CircleCheck, Van,
  TrendCharts, FolderOpened, DataLine, EditPen, Operation, Memo, Tickets,
  Expand, Fold
} from '@element-plus/icons-vue'

const { t } = useI18n()

const props = defineProps<{
  isCollapsed: boolean
  isMobile?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:isCollapsed', value: boolean): void
}>()

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const goHome = () => {
  router.push('/dashboard')
}

const handleMenuSelect = (index: string) => {
  router.push(index)
}

const toggleCollapse = () => {
  emit('update:isCollapsed', !props.isCollapsed)
}
</script>

<style scoped>
.sidebar-menu {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(180deg, #1a1f36 0%, #252b48 50%, #1a1f36 100%);
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 54px;
  gap: 10px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.15) 100%);
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.25) 100%);
}

.logo-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.logo:hover .logo-icon-wrapper {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #fff 0%, #e0e0ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-image {
  height: 40px;
  width: auto;
  object-fit: contain;
  transition: all 0.3s ease;
}

.logo:hover .logo-image {
  transform: scale(1.05);
  filter: drop-shadow(0 4px 8px rgba(102, 126, 234, 0.4));
}

.menu-scrollbar {
  flex: 1;
  overflow: hidden;
}

.sidebar-el-menu {
  border-right: none;
  padding: 4px 0;
  width: 100%;
  box-sizing: border-box;
}

.sidebar-el-menu:not(.el-menu--collapse) {
  width: 100%;
}

/* ========== 层级区分：一级父目录（ERP 直下的 販売/購買/受注/在庫/生産/出荷/原価） ========== */
:deep(.el-sub-menu > .el-sub-menu__title) {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95) !important;
  background: rgba(255, 255, 255, 0.06) !important;
  border-left: 3px solid rgba(102, 126, 234, 0.6);
  margin: 6px 8px 2px;
  padding-left: 12px !important;
  border-radius: 8px 0 0 8px;
}
:deep(.el-sub-menu > .el-sub-menu__title:hover) {
  background: rgba(102, 126, 234, 0.18) !important;
  border-left-color: rgba(102, 126, 234, 0.9);
}
:deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
  background: rgba(102, 126, 234, 0.12) !important;
  border-left-color: #667eea;
}

/* 一级父目录下的子菜单列表：增加上边距，与父标题视觉分组 */
:deep(.el-sub-menu > .el-sub-menu__list) {
  padding-top: 4px;
  padding-bottom: 8px;
  margin-bottom: 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
:deep(.el-sub-menu:last-child > .el-sub-menu__list) {
  border-bottom: none;
}

/* ========== 二级父目录（如 生産計画、生産指示、マスタリスト 等） ========== */
:deep(.el-sub-menu .el-sub-menu > .el-sub-menu__title) {
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85) !important;
  background: transparent !important;
  border-left: 2px solid rgba(255, 255, 255, 0.2);
  margin: 2px 0;
  padding-left: 36px !important;
  border-radius: 6px;
  font-size: 12.5px;
}
:deep(.el-sub-menu .el-sub-menu > .el-sub-menu__title:hover) {
  background: rgba(102, 126, 234, 0.12) !important;
  border-left-color: rgba(102, 126, 234, 0.5);
}
:deep(.el-sub-menu .el-sub-menu.is-opened > .el-sub-menu__title) {
  background: rgba(102, 126, 234, 0.08) !important;
  border-left-color: rgba(102, 126, 234, 0.7);
}

/* 二级父目录下的子项列表 */
:deep(.el-sub-menu .el-sub-menu > .el-sub-menu__list) {
  padding-top: 2px;
  padding-bottom: 4px;
  border-bottom: none;
  margin-bottom: 0;
}

/* Menu Items Styling - 叶子节点（最终可点击项） */
:deep(.el-menu-item) {
  height: 36px;
  line-height: 36px;
  margin: 2px 0;
  border-radius: 6px;
  font-size: 13px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  padding-left: 8px;
  width: 100%;
  box-sizing: border-box;
  color: rgba(255, 255, 255, 0.78);
}
/* 一级父目录下的直接子项 */
:deep(.el-sub-menu > .el-sub-menu__list > .el-menu-item) {
  padding-left: 35px !important;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.72);
}
/* 二级父目录下的子项（再缩进、略小字） */
:deep(.el-sub-menu .el-sub-menu .el-menu-item) {
  padding-left: 47px !important;
  font-size: 12.5px;
  color: rgba(255, 255, 255, 0.68);
}

:deep(.el-menu-item .el-menu-tooltip__trigger),
:deep(.el-menu-item > span) {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.el-sub-menu__title) {
  height: 38px;
  line-height: 38px;
  margin: 2px 0;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  padding-left: 8px;
  padding-right: 36px; /* 固定留出右侧箭头区域，避免与文字重叠 */
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
}

/* 标题内除箭头外的内容区域：限制宽度，防止挤到箭头 */
:deep(.el-sub-menu__title > span) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  flex: 1;
}

:deep(.el-sub-menu__title > .el-icon:not(.el-sub-menu__icon-arrow)) {
  flex-shrink: 0;
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(102, 126, 234, 0.15) !important;
  color: #fff !important;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: #fff !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}

:deep(.el-menu-item .el-icon),
:deep(.el-sub-menu__title > .el-icon:not(.el-sub-menu__icon-arrow)) {
  font-size: 16px;
  margin-right: 8px;
  flex-shrink: 0;
}

/* 下拉箭头固定在该行最右侧，绝对定位避免与文字重叠（排除标题里的菜单图标） */
:deep(.el-sub-menu__title > .el-sub-menu__icon-arrow) {
  position: absolute !important;
  right: 10px !important;
  left: auto !important;
  top: 50% !important;
  margin: 0 !important;
  margin-top: -6px !important;
  margin-right: 0 !important;
  display: inline-flex !important;
  align-items: center !important;
  flex: none !important;
  flex-shrink: 0 !important;
  width: auto !important;
}

:deep(.el-sub-menu .el-menu-item:hover) {
  color: #fff !important;
}

:deep(.el-sub-menu) {
  width: 100%;
}

/* Collapsed state：隐藏下拉箭头，图标居中 */
:deep(.el-menu--collapse) {
  width: 100%;
  padding: 4px 0;
  box-sizing: border-box;
}

:deep(.el-menu--collapse .el-menu-item),
:deep(.el-menu--collapse .el-sub-menu__title) {
  padding: 0 !important;
  justify-content: center !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}
/* 折叠时取消层级样式，保持图标行统一 */
:deep(.el-menu--collapse .el-sub-menu > .el-sub-menu__title),
:deep(.el-menu--collapse .el-sub-menu .el-sub-menu > .el-sub-menu__title) {
  margin: 2px 0 !important;
  border-left: none !important;
  background: transparent !important;
  border-radius: 8px !important;
}

:deep(.el-menu--collapse .el-sub-menu__icon-arrow) {
  display: none !important;
}

:deep(.el-menu--collapse .el-sub-menu__title > span) {
  display: none !important;
}

:deep(.el-menu--collapse .el-menu-item .el-icon),
:deep(.el-menu--collapse .el-sub-menu__title .el-icon) {
  margin-right: 0 !important;
  margin-left: 0 !important;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.08) 100%);
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.3s ease;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.collapse-btn:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.15) 100%);
  color: #fff;
}

.collapse-text {
  font-size: 12px;
  font-weight: 500;
}

/* Text fade animation */
.fade-text-enter-active,
.fade-text-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-text-enter-from,
.fade-text-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}

/* Scrollbar styling */
:deep(.el-scrollbar__bar.is-vertical) {
  width: 4px;
  right: 2px;
}

:deep(.el-scrollbar__thumb) {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

:deep(.el-scrollbar__thumb:hover) {
  background: rgba(255, 255, 255, 0.35);
}
</style>

<!-- Global styles for collapsed menu popup (teleported to body) -->
<style>
.el-menu--vertical.el-menu--popup-container .el-menu--popup {
  background: linear-gradient(180deg, #1a1f36 0%, #252b48 100%) !important;
  border: 1px solid rgba(102, 126, 234, 0.25) !important;
  border-radius: 10px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
  padding: 8px !important;
  min-width: 180px !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-menu-item {
  height: 36px !important;
  line-height: 36px !important;
  margin: 2px 0 !important;
  border-radius: 8px !important;
  color: rgba(255, 255, 255, 0.75) !important;
  font-size: 13px !important;
  padding: 0 14px !important;
  background: transparent !important;
  transition: all 0.2s ease !important;
  display: flex !important;
  align-items: center !important;
  min-width: 0 !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-menu-item .el-icon {
  flex-shrink: 0 !important;
  margin-right: 8px !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-menu-item > span,
.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-menu-item .el-menu-tooltip__trigger {
  min-width: 0 !important;
  flex: 1 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-menu-item:hover {
  background: rgba(102, 126, 234, 0.25) !important;
  color: #fff !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-menu-item.is-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.35) !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu__title {
  height: 36px !important;
  line-height: 36px !important;
  color: rgba(255, 255, 255, 0.75) !important;
  border-radius: 8px !important;
  padding: 0 36px 0 14px !important;
  background: transparent !important;
  transition: all 0.2s ease !important;
  display: flex !important;
  align-items: center !important;
  min-width: 0 !important;
  position: relative !important;
  overflow: hidden !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu__title .el-icon {
  flex-shrink: 0 !important;
  margin-right: 8px !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu__title > span {
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  min-width: 0 !important;
  flex: 1 !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu__title:hover {
  background: rgba(102, 126, 234, 0.25) !important;
  color: #fff !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu__title .el-icon {
  color: rgba(255, 255, 255, 0.7) !important;
}

.el-menu--vertical.el-menu--popup-container .el-sub-menu__icon-arrow {
  position: absolute !important;
  right: 10px !important;
  left: auto !important;
  top: 50% !important;
  margin: 0 !important;
  margin-top: -6px !important;
  flex-shrink: 0 !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu .el-menu {
  background: linear-gradient(180deg, #1a1f36 0%, #252b48 100%) !important;
  border: 1px solid rgba(102, 126, 234, 0.2) !important;
  border-radius: 8px !important;
  padding: 6px !important;
}

/* 折叠后所有层级弹出菜单项：图标与文字不重叠 */
.el-menu--vertical.el-menu--popup-container .el-menu-item {
  display: flex !important;
  align-items: center !important;
  min-width: 0 !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu-item .el-icon {
  flex-shrink: 0 !important;
  margin-right: 8px !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu-item > span,
.el-menu--vertical.el-menu--popup-container .el-menu-item .el-menu-tooltip__trigger {
  min-width: 0 !important;
  flex: 1 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}
</style>
