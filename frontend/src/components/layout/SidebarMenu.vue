<template>
  <div class="sidebar-menu">
    <!-- Logo -->
    <div class="logo" @click="goHome">
      <div class="logo-icon-wrapper">
        <el-icon :size="isCollapsed ? 22 : 24"><DataBoard /></el-icon>
      </div>
      <transition name="fade-text">
        <span v-if="!isCollapsed" class="logo-text">Smart-EMAP</span>
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
          <template #title>{{ t('menu.DASHBOARD') }}</template>
        </el-menu-item>
        
        <el-sub-menu index="erp">
          <template #title>
            <el-icon><Management /></el-icon>
            <span>{{ t('menu.ERP') }}</span>
          </template>
          
          <el-sub-menu index="erp-sales">
            <template #title>
              <el-icon><Sell /></el-icon>
              <span>{{ t('menu.ERP_SALES') }}</span>
            </template>
            <el-menu-item index="/erp/sales">{{ t('menu.ERP_SALES_HOME') }}</el-menu-item>
            <el-menu-item index="/erp/sales/quotation">{{ t('menu.ERP_SALES_QUOTATION') }}</el-menu-item>
            <el-menu-item index="/erp/sales/orders">{{ t('menu.ERP_SALES_ORDERS') }}</el-menu-item>
            <el-menu-item index="/erp/sales/edi-import">{{ t('menu.ERP_SALES_EDI') }}</el-menu-item>
            <el-menu-item index="/erp/sales/shipping">{{ t('menu.ERP_SALES_SHIPPING') }}</el-menu-item>
            <el-menu-item index="/erp/sales/recording">{{ t('menu.ERP_SALES_RECORDING') }}</el-menu-item>
            <el-menu-item index="/erp/sales/returns">{{ t('menu.ERP_SALES_RETURNS') }}</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="erp-purchase">
            <template #title>
              <el-icon><ShoppingCart /></el-icon>
              <span>{{ t('menu.ERP_PURCHASE') }}</span>
            </template>
            <el-menu-item index="/erp/purchase">{{ t('menu.ERP_PURCHASE_HOME') }}</el-menu-item>
            <el-menu-item index="/erp/purchase/orders">{{ t('menu.ERP_PURCHASE_ORDERS') }}</el-menu-item>
            <el-menu-item index="/erp/purchase/rfq">{{ t('menu.ERP_PURCHASE_RFQ') }}</el-menu-item>
            <el-menu-item index="/erp/purchase/arrival">{{ t('menu.ERP_PURCHASE_ARRIVAL') }}</el-menu-item>
            <el-menu-item index="/erp/purchase/receipt">{{ t('menu.ERP_PURCHASE_RECEIPT') }}</el-menu-item>
            <el-menu-item index="/erp/purchase/invoice-matching">{{ t('menu.ERP_PURCHASE_INVOICE') }}</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="erp-inventory">
            <template #title>
              <el-icon><Box /></el-icon>
              <span>{{ t('menu.ERP_INVENTORY') }}</span>
            </template>
            <el-menu-item index="/erp/inventory">{{ t('menu.ERP_INVENTORY_HOME') }}</el-menu-item>
            <el-menu-item index="/erp/inventory/list">{{ t('menu.ERP_INVENTORY_LIST') }}</el-menu-item>
            <el-menu-item index="/erp/inventory/transactions">{{ t('menu.ERP_INVENTORY_TX') }}</el-menu-item>
            <el-menu-item index="/erp/inventory/movement">{{ t('menu.ERP_INVENTORY_MOVEMENT') }}</el-menu-item>
            <el-menu-item index="/erp/inventory/stocktaking">{{ t('menu.ERP_INVENTORY_STOCKTAKING') }}</el-menu-item>
            <el-menu-item index="/erp/inventory/dead-stock">{{ t('menu.ERP_INVENTORY_DEAD') }}</el-menu-item>
            <el-menu-item index="/erp/inventory/abc-analysis">{{ t('menu.ERP_INVENTORY_ABC') }}</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="erp-costing">
            <template #title>
              <el-icon><Coin /></el-icon>
              <span>{{ t('menu.ERP_COSTING') }}</span>
            </template>
            <el-menu-item index="/erp/costing">{{ t('menu.ERP_COSTING_HOME') }}</el-menu-item>
            <el-menu-item index="/erp/costing/standard">{{ t('menu.ERP_COSTING_STANDARD') }}</el-menu-item>
            <el-menu-item index="/erp/costing/actual">{{ t('menu.ERP_COSTING_ACTUAL') }}</el-menu-item>
            <el-menu-item index="/erp/costing/variance">{{ t('menu.ERP_COSTING_VARIANCE') }}</el-menu-item>
            <el-menu-item index="/erp/costing/billing">{{ t('menu.ERP_COSTING_BILLING') }}</el-menu-item>
            <el-menu-item index="/erp/costing/payment">{{ t('menu.ERP_COSTING_PAYMENT') }}</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="erp-order">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>{{ t('menu.ERP_ORDER') }}</span>
            </template>
            <el-menu-item index="/erp/order">{{ t('menu.ERP_ORDER_HOME') }}</el-menu-item>
            <el-menu-item index="/erp/order/monthly">{{ t('menu.ERP_ORDER_MONTHLY') }}</el-menu-item>
            <el-menu-item index="/erp/order/daily">{{ t('menu.ERP_ORDER_DAILY') }}</el-menu-item>
            <el-menu-item index="/erp/order/dashboard">{{ t('menu.ERP_ORDER_DASHBOARD') }}</el-menu-item>
            <el-menu-item index="/erp/order/kpi">{{ t('menu.ERP_ORDER_KPI') }}</el-menu-item>
            <el-menu-item index="/erp/order/daily-history">{{ t('menu.ERP_ORDER_DAILY_HIST') }}</el-menu-item>
            <el-menu-item index="/erp/order/customer-history">{{ t('menu.ERP_ORDER_CUSTOMER_HIST') }}</el-menu-item>
            <el-menu-item index="/erp/order/destination-history">{{ t('menu.ERP_ORDER_DEST_HIST') }}</el-menu-item>
            <el-menu-item index="/erp/order/comparison">{{ t('menu.ERP_ORDER_COMPARISON') }}</el-menu-item>
            <el-menu-item index="/erp/order/print">{{ t('menu.ERP_ORDER_PRINT') }}</el-menu-item>
          </el-sub-menu>
          
          <el-menu-item index="/erp/supplier">
            <el-icon><User /></el-icon>
            <template #title>{{ t('menu.ERP_SUPPLIER') }}</template>
          </el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="aps">
          <template #title>
            <el-icon><DataAnalysis /></el-icon>
            <span>{{ t('menu.APS') }}</span>
          </template>
          <el-menu-item index="/aps/planning">{{ t('menu.APS_PLANNING') }}</el-menu-item>
          <el-menu-item index="/aps/scheduling">{{ t('menu.APS_SCHEDULING') }}</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="mes">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>{{ t('menu.MES') }}</span>
          </template>
          <el-menu-item index="/mes/execution">{{ t('menu.MES_EXECUTION') }}</el-menu-item>
          <el-menu-item index="/mes/quality">{{ t('menu.MES_QUALITY') }}</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="master">
          <template #title>
            <el-icon><Collection /></el-icon>
            <span>{{ t('menu.MASTER') }}</span>
          </template>
          <el-sub-menu index="master-list">
            <template #title>{{ t('menu.MASTER_LIST') }}</template>
            <el-menu-item index="/master/product">{{ t('menu.MASTER_PRODUCT') }}</el-menu-item>
            <el-menu-item index="/master/material">{{ t('menu.MASTER_MATERIAL') }}</el-menu-item>
            <el-menu-item index="/master/supplier">{{ t('menu.MASTER_SUPPLIER') }}</el-menu-item>
            <el-menu-item index="/master/process-route">{{ t('menu.MASTER_PROCESS_ROUTE') }}</el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/master/bom">{{ t('menu.MASTER_BOM') }}</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu v-if="userStore.hasPermission('all')" index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>{{ t('menu.SYSTEM') }}</span>
          </template>
          
          <el-sub-menu index="system-user">
            <template #title>
              <el-icon><User /></el-icon>
              <span>{{ t('menu.SYSTEM_USER') }}</span>
            </template>
            <el-menu-item index="/system">{{ t('menu.SYSTEM_HOME') }}</el-menu-item>
            <el-menu-item index="/system/users">{{ t('menu.SYSTEM_USERS') }}</el-menu-item>
            <el-menu-item index="/system/organization">{{ t('menu.SYSTEM_ORG') }}</el-menu-item>
            <el-menu-item index="/system/roles">{{ t('menu.SYSTEM_ROLE') }}</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="system-settings">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span>{{ t('menu.SYSTEM_SETTINGS') }}</span>
            </template>
            <el-menu-item index="/system/numbering">{{ t('menu.SYSTEM_NUMBERING') }}</el-menu-item>
            <el-menu-item index="/system/workflow">{{ t('menu.SYSTEM_WORKFLOW') }}</el-menu-item>
            <el-menu-item index="/system/notification">{{ t('menu.SYSTEM_NOTIFICATION') }}</el-menu-item>
            <el-menu-item index="/system/logs">{{ t('menu.SYSTEM_LOGS') }}</el-menu-item>
            <el-menu-item index="/system/data">{{ t('menu.SYSTEM_DATA') }}</el-menu-item>
            <el-menu-item index="/system/menus">{{ t('menu.SYSTEM_MENUS') }}</el-menu-item>
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
  Collection
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

.menu-scrollbar {
  flex: 1;
  overflow: hidden;
}

.sidebar-el-menu {
  border-right: none;
  padding: 6px 8px;
}

.sidebar-el-menu:not(.el-menu--collapse) {
  width: 210px;
}

/* Menu Items Styling */
:deep(.el-menu-item) {
  height: 38px;
  line-height: 38px;
  margin: 2px 0;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.2s ease;
}

:deep(.el-sub-menu__title) {
  height: 38px;
  line-height: 38px;
  margin: 2px 0;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.2s ease;
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
:deep(.el-sub-menu__title .el-icon) {
  font-size: 16px;
  margin-right: 8px;
}

:deep(.el-sub-menu .el-menu-item) {
  padding-left: 48px !important;
  color: rgba(255, 255, 255, 0.65);
}

:deep(.el-sub-menu .el-sub-menu .el-menu-item) {
  padding-left: 64px !important;
}

:deep(.el-sub-menu .el-menu-item:hover) {
  color: #fff !important;
}

/* Collapsed state */
:deep(.el-menu--collapse) {
  width: 56px;
  padding: 6px 4px;
}

:deep(.el-menu--collapse .el-menu-item),
:deep(.el-menu--collapse .el-sub-menu__title) {
  padding: 0 !important;
  justify-content: center;
}

:deep(.el-menu--collapse .el-menu-item .el-icon),
:deep(.el-menu--collapse .el-sub-menu__title .el-icon) {
  margin-right: 0;
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
  padding: 0 14px !important;
  background: transparent !important;
  transition: all 0.2s ease !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu__title:hover {
  background: rgba(102, 126, 234, 0.25) !important;
  color: #fff !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu__title .el-icon {
  color: rgba(255, 255, 255, 0.7) !important;
}

.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu .el-menu {
  background: linear-gradient(180deg, #1a1f36 0%, #252b48 100%) !important;
  border: 1px solid rgba(102, 126, 234, 0.2) !important;
  border-radius: 8px !important;
  padding: 6px !important;
}
</style>
