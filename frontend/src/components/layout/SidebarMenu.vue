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
            <el-menu-item index="/erp/sales"><span :title="t('menu.ERP_SALES_HOME')">{{ t('menu.ERP_SALES_HOME') }}</span></el-menu-item>
            <el-menu-item index="/erp/sales/quotation"><span :title="t('menu.ERP_SALES_QUOTATION')">{{ t('menu.ERP_SALES_QUOTATION') }}</span></el-menu-item>
            <el-menu-item index="/erp/sales/orders"><span :title="t('menu.ERP_SALES_ORDERS')">{{ t('menu.ERP_SALES_ORDERS') }}</span></el-menu-item>
            <el-menu-item index="/erp/sales/forecast"><span :title="t('menu.ERP_SALES_FORECAST')">{{ t('menu.ERP_SALES_FORECAST') }}</span></el-menu-item>
            <el-menu-item index="/erp/sales/credit"><span :title="t('menu.ERP_SALES_CREDIT')">{{ t('menu.ERP_SALES_CREDIT') }}</span></el-menu-item>
            <el-menu-item index="/erp/sales/contract-pricing"><span :title="t('menu.ERP_SALES_CONTRACT')">{{ t('menu.ERP_SALES_CONTRACT') }}</span></el-menu-item>
            <el-menu-item index="/erp/sales/shipping"><span :title="t('menu.ERP_SALES_SHIPPING')">{{ t('menu.ERP_SALES_SHIPPING') }}</span></el-menu-item>
            <el-menu-item index="/erp/sales/recording"><span :title="t('menu.ERP_SALES_RECORDING')">{{ t('menu.ERP_SALES_RECORDING') }}</span></el-menu-item>
            <el-menu-item index="/erp/sales/invoice"><span :title="t('menu.ERP_SALES_INVOICE')">{{ t('menu.ERP_SALES_INVOICE') }}</span></el-menu-item>
            <el-menu-item index="/erp/sales/return-correction"><span :title="t('menu.ERP_SALES_CORRECTION')">{{ t('menu.ERP_SALES_CORRECTION') }}</span></el-menu-item>
            <el-menu-item index="/erp/sales/returns"><span :title="t('menu.ERP_SALES_RETURNS')">{{ t('menu.ERP_SALES_RETURNS') }}</span></el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="erp-purchase">
            <template #title>
              <el-icon><ShoppingCart /></el-icon>
              <span :title="t('menu.ERP_PURCHASE')">{{ t('menu.ERP_PURCHASE') }}</span>
            </template>
            <el-menu-item index="/erp/purchase"><span :title="t('menu.ERP_PURCHASE_HOME')">{{ t('menu.ERP_PURCHASE_HOME') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/orders"><span :title="t('menu.ERP_PURCHASE_ORDERS')">{{ t('menu.ERP_PURCHASE_ORDERS') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/rfq"><span :title="t('menu.ERP_PURCHASE_RFQ')">{{ t('menu.ERP_PURCHASE_RFQ') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/subcontract-order"><span :title="t('menu.ERP_PURCHASE_SUBCONTRACT')">{{ t('menu.ERP_PURCHASE_SUBCONTRACT') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/material-supply"><span :title="t('menu.ERP_PURCHASE_SUPPLY')">{{ t('menu.ERP_PURCHASE_SUPPLY') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/subcontract-inventory"><span :title="t('menu.ERP_PURCHASE_SUB_INV')">{{ t('menu.ERP_PURCHASE_SUB_INV') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/arrival"><span :title="t('menu.ERP_PURCHASE_ARRIVAL')">{{ t('menu.ERP_PURCHASE_ARRIVAL') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/receipt"><span :title="t('menu.ERP_PURCHASE_RECEIPT')">{{ t('menu.ERP_PURCHASE_RECEIPT') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/inspection"><span :title="t('menu.ERP_PURCHASE_INSPECTION')">{{ t('menu.ERP_PURCHASE_INSPECTION') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/invoice-matching"><span :title="t('menu.ERP_PURCHASE_INVOICE')">{{ t('menu.ERP_PURCHASE_INVOICE') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/payment-schedule"><span :title="t('menu.ERP_PURCHASE_PAY_SCHEDULE')">{{ t('menu.ERP_PURCHASE_PAY_SCHEDULE') }}</span></el-menu-item>
            <el-menu-item index="/erp/purchase/bank-transfer"><span :title="t('menu.ERP_PURCHASE_BANK')">{{ t('menu.ERP_PURCHASE_BANK') }}</span></el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="erp-order">
            <template #title>
              <el-icon><Document /></el-icon>
              <span :title="t('menu.ERP_ORDER')">{{ t('menu.ERP_ORDER') }}</span>
            </template>
            <el-menu-item index="/erp/order"><span :title="t('menu.ERP_ORDER_HOME')">{{ t('menu.ERP_ORDER_HOME') }}</span></el-menu-item>
            <el-menu-item index="/erp/order/monthly"><span :title="t('menu.ERP_ORDER_MONTHLY')">{{ t('menu.ERP_ORDER_MONTHLY') }}</span></el-menu-item>
            <el-menu-item index="/erp/order/daily"><span :title="t('menu.ERP_ORDER_DAILY')">{{ t('menu.ERP_ORDER_DAILY') }}</span></el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="erp-inventory">
            <template #title>
              <el-icon><Box /></el-icon>
              <span :title="t('menu.ERP_INVENTORY')">{{ t('menu.ERP_INVENTORY') }}</span>
            </template>
            <el-menu-item index="/erp/inventory"><span :title="t('menu.ERP_INVENTORY_HOME')">{{ t('menu.ERP_INVENTORY_HOME') }}</span></el-menu-item>
            <el-menu-item index="/erp/inventory/list"><span :title="t('menu.ERP_INVENTORY_LIST')">{{ t('menu.ERP_INVENTORY_LIST') }}</span></el-menu-item>
            <el-menu-item index="/erp/inventory/location"><span :title="t('menu.ERP_INVENTORY_LOCATION')">{{ t('menu.ERP_INVENTORY_LOCATION') }}</span></el-menu-item>
            <el-menu-item index="/erp/inventory/transactions"><span :title="t('menu.ERP_INVENTORY_TX')">{{ t('menu.ERP_INVENTORY_TX') }}</span></el-menu-item>
            <el-menu-item index="/erp/inventory/movement"><span :title="t('menu.ERP_INVENTORY_MOVEMENT')">{{ t('menu.ERP_INVENTORY_MOVEMENT') }}</span></el-menu-item>
            <el-menu-item index="/erp/inventory/lot-trace"><span :title="t('menu.ERP_INVENTORY_LOT')">{{ t('menu.ERP_INVENTORY_LOT') }}</span></el-menu-item>
            <el-menu-item index="/erp/inventory/stocktaking"><span :title="t('menu.ERP_INVENTORY_STOCKTAKING')">{{ t('menu.ERP_INVENTORY_STOCKTAKING') }}</span></el-menu-item>
            <el-menu-item index="/erp/inventory/dead-stock"><span :title="t('menu.ERP_INVENTORY_DEAD')">{{ t('menu.ERP_INVENTORY_DEAD') }}</span></el-menu-item>
            <el-menu-item index="/erp/inventory/abc-analysis"><span :title="t('menu.ERP_INVENTORY_ABC')">{{ t('menu.ERP_INVENTORY_ABC') }}</span></el-menu-item>
            <el-menu-item index="/erp/inventory/stock-transaction-logs"><span :title="t('menu.ERP_INVENTORY_STOCK_TX_LOG')">{{ t('menu.ERP_INVENTORY_STOCK_TX_LOG') }}</span></el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="erp-production">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span :title="t('menu.ERP_PRODUCTION')">{{ t('menu.ERP_PRODUCTION') }}</span>
            </template>
            <el-menu-item index="/erp/production"><span :title="t('menu.ERP_PRODUCTION_HOME')">{{ t('menu.ERP_PRODUCTION_HOME') }}</span></el-menu-item>
            <el-menu-item index="/erp/production/eco"><span :title="t('menu.ERP_PRODUCTION_ECO')">{{ t('menu.ERP_PRODUCTION_ECO') }}</span></el-menu-item>
            <el-menu-item index="/erp/production/bom"><span :title="t('menu.ERP_PRODUCTION_BOM')">{{ t('menu.ERP_PRODUCTION_BOM') }}</span></el-menu-item>
            <el-menu-item index="/erp/production/mrp"><span :title="t('menu.ERP_PRODUCTION_MRP')">{{ t('menu.ERP_PRODUCTION_MRP') }}</span></el-menu-item>
            <el-menu-item index="/erp/production/orders"><span :title="t('menu.ERP_PRODUCTION_ORDERS')">{{ t('menu.ERP_PRODUCTION_ORDERS') }}</span></el-menu-item>
            <el-menu-item index="/erp/production/serial"><span :title="t('menu.ERP_PRODUCTION_SERIAL')">{{ t('menu.ERP_PRODUCTION_SERIAL') }}</span></el-menu-item>
            <el-menu-item index="/erp/production/data-management"><span :title="t('menu.ERP_PRODUCTION_DATA')">{{ t('menu.ERP_PRODUCTION_DATA') }}</span></el-menu-item>
            <el-menu-item index="/erp/production/work-order"><span :title="t('menu.ERP_PRODUCTION_WO')">{{ t('menu.ERP_PRODUCTION_WO') }}</span></el-menu-item>
            <el-menu-item index="/erp/production/material-issue"><span :title="t('menu.ERP_PRODUCTION_ISSUE')">{{ t('menu.ERP_PRODUCTION_ISSUE') }}</span></el-menu-item>
            <el-menu-item index="/erp/production/completion"><span :title="t('menu.ERP_PRODUCTION_COMPLETE')">{{ t('menu.ERP_PRODUCTION_COMPLETE') }}</span></el-menu-item>
            <el-menu-item index="/erp/production/consumption"><span :title="t('menu.ERP_PRODUCTION_CONSUME')">{{ t('menu.ERP_PRODUCTION_CONSUME') }}</span></el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="erp-costing">
            <template #title>
              <el-icon><Coin /></el-icon>
              <span :title="t('menu.ERP_COSTING')">{{ t('menu.ERP_COSTING') }}</span>
            </template>
            <el-menu-item index="/erp/costing"><span :title="t('menu.ERP_COSTING_HOME')">{{ t('menu.ERP_COSTING_HOME') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/standard"><span :title="t('menu.ERP_COSTING_STANDARD')">{{ t('menu.ERP_COSTING_STANDARD') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/actual"><span :title="t('menu.ERP_COSTING_ACTUAL')">{{ t('menu.ERP_COSTING_ACTUAL') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/variance"><span :title="t('menu.ERP_COSTING_VARIANCE')">{{ t('menu.ERP_COSTING_VARIANCE') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/allocation"><span :title="t('menu.ERP_COSTING_ALLOCATION')">{{ t('menu.ERP_COSTING_ALLOCATION') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/wip"><span :title="t('menu.ERP_COSTING_WIP')">{{ t('menu.ERP_COSTING_WIP') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/equipment"><span :title="t('menu.ERP_COSTING_EQUIPMENT')">{{ t('menu.ERP_COSTING_EQUIPMENT') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/depreciation"><span :title="t('menu.ERP_COSTING_DEPRECIATION')">{{ t('menu.ERP_COSTING_DEPRECIATION') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/journal"><span :title="t('menu.ERP_COSTING_JOURNAL')">{{ t('menu.ERP_COSTING_JOURNAL') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/accounting-export"><span :title="t('menu.ERP_COSTING_ACCT_EXPORT')">{{ t('menu.ERP_COSTING_ACCT_EXPORT') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/billing"><span :title="t('menu.ERP_COSTING_BILLING')">{{ t('menu.ERP_COSTING_BILLING') }}</span></el-menu-item>
            <el-menu-item index="/erp/costing/payment"><span :title="t('menu.ERP_COSTING_PAYMENT')">{{ t('menu.ERP_COSTING_PAYMENT') }}</span></el-menu-item>
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
            <el-menu-item index="/master"><span :title="t('menu.MASTER_HOME')">{{ t('menu.MASTER_HOME') }}</span></el-menu-item>
            <el-menu-item index="/master/product"><span :title="t('menu.MASTER_PRODUCT')">{{ t('menu.MASTER_PRODUCT') }}</span></el-menu-item>
            <el-menu-item index="/master/material"><span :title="t('menu.MASTER_MATERIAL')">{{ t('menu.MASTER_MATERIAL') }}</span></el-menu-item>
            <el-menu-item index="/master/customer"><span :title="t('menu.MASTER_CUSTOMER')">{{ t('menu.MASTER_CUSTOMER') }}</span></el-menu-item>
            <el-menu-item index="/master/supplier"><span :title="t('menu.MASTER_SUPPLIER')">{{ t('menu.MASTER_SUPPLIER') }}</span></el-menu-item>
            <el-menu-item index="/master/destination"><span :title="t('menu.MASTER_DESTINATION')">{{ t('menu.MASTER_DESTINATION') }}</span></el-menu-item>
            <el-menu-item index="/master/destination/holiday"><span :title="t('menu.MASTER_DESTINATION_HOLIDAY')">{{ t('menu.MASTER_DESTINATION_HOLIDAY') }}</span></el-menu-item>
            <el-menu-item index="/master/carrier"><span :title="t('menu.MASTER_CARRIER')">{{ t('menu.MASTER_CARRIER') }}</span></el-menu-item>
            <el-menu-item index="/master/machine"><span :title="t('menu.MASTER_MACHINE')">{{ t('menu.MASTER_MACHINE') }}</span></el-menu-item>
            <el-menu-item index="/master/process"><span :title="t('menu.MASTER_PROCESS')">{{ t('menu.MASTER_PROCESS') }}</span></el-menu-item>
            <el-menu-item index="/master/process-route"><span :title="t('menu.MASTER_PROCESS_ROUTE')">{{ t('menu.MASTER_PROCESS_ROUTE') }}</span></el-menu-item>
            <el-menu-item index="/master/product-process-route"><span :title="t('menu.MASTER_PRODUCT_PROCESS_ROUTE')">{{ t('menu.MASTER_PRODUCT_PROCESS_ROUTE') }}</span></el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="master-bom">
            <template #title>
              <el-icon><Connection /></el-icon>
              <span :title="t('menu.MASTER_BOM')">{{ t('menu.MASTER_BOM') }}</span>
            </template>
            <el-menu-item index="/master/bom"><span :title="t('menu.MASTER_BOM_HOME')">{{ t('menu.MASTER_BOM_HOME') }}</span></el-menu-item>
            <el-menu-item index="/master/bom/product-process"><span :title="t('menu.MASTER_PRODUCT_PROCESS_BOM')">{{ t('menu.MASTER_PRODUCT_PROCESS_BOM') }}</span></el-menu-item>
            <el-menu-item index="/master/bom/product-machine-config"><span :title="t('menu.MASTER_PRODUCT_MACHINE_CONFIG')">{{ t('menu.MASTER_PRODUCT_MACHINE_CONFIG') }}</span></el-menu-item>
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
            <el-menu-item index="/system"><span :title="t('menu.SYSTEM_HOME')">{{ t('menu.SYSTEM_HOME') }}</span></el-menu-item>
            <el-menu-item index="/system/users"><span :title="t('menu.SYSTEM_USERS')">{{ t('menu.SYSTEM_USERS') }}</span></el-menu-item>
            <el-menu-item index="/system/organization"><span :title="t('menu.SYSTEM_ORG')">{{ t('menu.SYSTEM_ORG') }}</span></el-menu-item>
            <el-menu-item index="/system/roles"><span :title="t('menu.SYSTEM_ROLE')">{{ t('menu.SYSTEM_ROLE') }}</span></el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="system-settings">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span :title="t('menu.SYSTEM_SETTINGS')">{{ t('menu.SYSTEM_SETTINGS') }}</span>
            </template>
            <el-menu-item index="/system/numbering"><span :title="t('menu.SYSTEM_NUMBERING')">{{ t('menu.SYSTEM_NUMBERING') }}</span></el-menu-item>
            <el-menu-item index="/system/workflow"><span :title="t('menu.SYSTEM_WORKFLOW')">{{ t('menu.SYSTEM_WORKFLOW') }}</span></el-menu-item>
            <el-menu-item index="/system/notification"><span :title="t('menu.SYSTEM_NOTIFICATION')">{{ t('menu.SYSTEM_NOTIFICATION') }}</span></el-menu-item>
            <el-menu-item index="/system/logs"><span :title="t('menu.SYSTEM_LOGS')">{{ t('menu.SYSTEM_LOGS') }}</span></el-menu-item>
            <el-menu-item index="/system/data"><span :title="t('menu.SYSTEM_DATA')">{{ t('menu.SYSTEM_DATA') }}</span></el-menu-item>
            <el-menu-item index="/system/menus"><span :title="t('menu.SYSTEM_MENUS')">{{ t('menu.SYSTEM_MENUS') }}</span></el-menu-item>
            <el-menu-item index="/system/file-watcher"><span :title="t('menu.SYSTEM_FILE_WATCHER')">{{ t('menu.SYSTEM_FILE_WATCHER') }}</span></el-menu-item>
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
  Collection, List, Connection, Calendar, Timer, VideoPlay, CircleCheck
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

/* Menu Items Styling - 图标与文字并排，长文本省略防重叠，行宽填满侧栏 */
:deep(.el-menu-item) {
  height: 38px;
  line-height: 38px;
  margin: 2px 0;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  padding-left: 8px;
  width: 100%;
  box-sizing: border-box;
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

:deep(.el-sub-menu .el-menu-item) {
  padding-left: 40px !important;
  color: rgba(255, 255, 255, 0.65);
}

:deep(.el-sub-menu .el-sub-menu .el-menu-item) {
  padding-left: 52px !important;
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
