<template>
  <div class="sidebar-menu">
    <!-- Logo -->
    <div class="logo" @click="goHome">
      <transition name="fade-text">
        <img v-if="!isCollapsed" src="/logo.png" alt="Smart-EMAP" class="logo-image" />
        <div v-else class="logo-icon-wrapper">
          <img src="/favicon.ico" alt="Smart-EMAP" class="logo-favicon" />
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
        <el-menu-item
          v-if="canAccessMenuCode('DASHBOARD')"
          index="/dashboard"
          class="menu-item-home menu-item-top"
        >
          <SidebarCollapsedEntry
            code="DASHBOARD"
            :label="t('menu.DASHBOARD')"
            :is-collapsed="isCollapsed"
          >
            <el-icon><HomeFilled /></el-icon>
          </SidebarCollapsedEntry>
        </el-menu-item>

        <MenuTreeItem
          v-for="section in visibleRootMenus"
          :key="section.code"
          :node="section"
          :is-collapsed="isCollapsed"
        />
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
import { buildTree, type MenuTreeNode } from '@/composables/useMenuTree'
import { useMenuPermissions } from '@/composables/useMenuPermissions'
import { SIDEBAR_ROOT_MENU_CODES } from '@/config/sidebarMenu'
import MenuTreeItem from '@/components/layout/MenuTreeItem.vue'
import SidebarCollapsedEntry from '@/components/layout/SidebarCollapsedEntry.vue'
import { HomeFilled, Expand, Fold } from '@element-plus/icons-vue'

const { t } = useI18n()

const { canAccessMenuCode, filterMenuTree } = useMenuPermissions()

const visibleRootMenus = computed(() =>
  SIDEBAR_ROOT_MENU_CODES
    .map((code) => filterMenuTree(buildTree(code)))
    .filter((node): node is MenuTreeNode => node != null),
)

const props = defineProps<{
  isCollapsed: boolean
  isMobile?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:isCollapsed', value: boolean): void
}>()

const router = useRouter()
const route = useRoute()

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

.logo-favicon {
  width: 22px;
  height: 22px;
  object-fit: contain;
  transition: all 0.3s ease;
}

.logo:hover .logo-image {
  transform: scale(1.05);
  filter: drop-shadow(0 4px 8px rgba(102, 126, 234, 0.4));
}

.logo:hover .logo-favicon {
  transform: scale(1.05);
  filter: drop-shadow(0 4px 8px rgba(102, 126, 234, 0.4));
}

.menu-scrollbar {
  flex: 1;
  overflow: hidden;
}

/* 减小子菜单缩进：覆盖 Element Plus 的菜单缩进变量（默认各 20px），子项往左收 */
:deep(.sidebar-el-menu) {
  --el-menu-base-level-padding: 10px;
  --el-menu-level-padding: 10px;
  border-right: none;
  padding: 4px 5px 4px 8px;
  width: 100%;
  box-sizing: border-box;
}

:deep(.sidebar-el-menu:not(.el-menu--collapse)) {
  width: 100%;
}

/* ========== 各层级菜单用颜色区分 ========== */
/* 顶级菜单项（Dashboard）— 与下方 ERP/APS 等父菜单标题左对齐 */
:deep(.sidebar-el-menu > .el-menu-item.menu-item-top) {
  height: 42px;
  line-height: 42px;
  margin: 8px 6px 8px 0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  padding-left: 6px !important; /* 4px 边框 + 6px，与 el-sub-menu__title 一致 */
  color: #ffffff !important;
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.12) 0%, rgba(102, 126, 234, 0.06) 100%) !important;
  border-left: 4px solid rgba(102, 126, 234, 0.8);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  justify-content: flex-start !important;
}

:deep(.sidebar-el-menu > .el-menu-item.menu-item-top .el-menu-tooltip__trigger) {
  display: flex !important;
  align-items: center !important;
  width: 100%;
  padding: 0 !important;
}

:deep(.sidebar-el-menu > .el-menu-item.menu-item-top .sidebar-collapsed-entry) {
  flex: 1;
  min-width: 0;
}

:deep(.sidebar-el-menu > .el-menu-item.menu-item-top .sidebar-collapsed-entry .el-icon) {
  margin-right: 0 !important;
}

:deep(.sidebar-el-menu > .el-menu-item.menu-item-top:hover) {
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.22) 0%, rgba(102, 126, 234, 0.12) 100%) !important;
  border-left-color: #667eea;
  box-shadow: 0 3px 12px rgba(102, 126, 234, 0.2);
}

/* 带「ホーム」的菜单项 - 橘黄色（含选中态）；需覆盖各层级叶子的白色，故提高特异性 */
:deep(.sidebar-el-menu .menu-item-home),
:deep(.sidebar-el-menu .menu-item-home .el-menu-tooltip__trigger),
:deep(.sidebar-el-menu .menu-item-home.is-active),
:deep(.sidebar-el-menu .menu-item-home.is-active .el-menu-tooltip__trigger) {
  color: #f8f66b !important;
  font-weight: 700 !important;
}
/* 購買・外注管理下二级子菜单内的ホーム（材料管理ホーム、外注ホーム） */
:deep(.sidebar-el-menu .el-sub-menu .el-sub-menu .el-sub-menu .el-menu-item.menu-item-home),
:deep(.sidebar-el-menu .el-sub-menu .el-sub-menu .el-sub-menu .el-menu-item.menu-item-home .el-menu-tooltip__trigger),
:deep(.sidebar-el-menu .el-sub-menu .el-sub-menu .el-sub-menu .el-menu-item.menu-item-home.is-active),
:deep(.sidebar-el-menu .el-sub-menu .el-sub-menu .el-sub-menu .el-menu-item.menu-item-home.is-active .el-menu-tooltip__trigger) {
  color: #f8f66b !important;
  font-weight: 700 !important;
}

/* 顶级父菜单标题(ERP/APS等) - 白色 + 蓝紫左边框，与顶级菜单项左对齐 */
:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__title) {
  height: 42px;
  line-height: 42px;
  font-size: 14px;
  font-weight: 700;
  margin: 8px 6px 8px 0;
  color: #ffffff !important;
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.12) 0%, rgba(102, 126, 234, 0.06) 100%) !important;
  border-left: 4px solid rgba(102, 126, 234, 0.8);
  border-radius: 8px;
  padding-left: 6px !important; /* 4px 边框 + 6px = 10px，与顶级菜单项图标列对齐 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  justify-content: flex-start !important;
}

:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__title:hover) {
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.22) 0%, rgba(102, 126, 234, 0.12) 100%) !important;
  border-left-color: #667eea;
  box-shadow: 0 3px 12px rgba(102, 126, 234, 0.2);
}

:deep(.sidebar-el-menu > .el-sub-menu.is-opened > .el-sub-menu__title) {
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.18) 0%, rgba(102, 126, 234, 0.08) 100%) !important;
  border-left-color: #667eea;
}

/* 顶级菜单下的子菜单列表容器 */
:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__list) {
  padding-top: 6px;
  padding-bottom: 10px;
  margin-bottom: 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 0 0 8px 8px;
}

/* 一级父目录(販売/購買/出荷等) - 青蓝色 */
:deep(.el-sub-menu > .el-sub-menu__title) {
  font-weight: 600;
  font-size: 13.5px;
  color: #93c5fd !important;
  background: rgba(147, 197, 253, 0.08) !important;
  border-left: 4px solid rgba(147, 197, 253, 0.7);
  margin: 6px 8px 3px;
  padding-left: 6px !important;
  border-radius: 8px 0 0 8px;
}

:deep(.el-sub-menu > .el-sub-menu__title:hover) {
  background: rgba(147, 197, 253, 0.18) !important;
  border-left-color: #93c5fd;
}

:deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
  background: rgba(147, 197, 253, 0.12) !important;
  border-left-color: #93c5fd;
}

/* 一级父目录下的子菜单列表：增加上边距，与父标题视觉分组；减小左侧缩进 */
:deep(.el-sub-menu > .el-sub-menu__list) {
  padding-top: 5px;
  padding-bottom: 8px;
  padding-left: 0;
  margin-bottom: 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

:deep(.el-sub-menu:last-child > .el-sub-menu__list) {
  border-bottom: none;
}

/* 二级父目录(生産計画、生産指示等) - 青绿色 */
:deep(.el-sub-menu .el-sub-menu > .el-sub-menu__title) {
  font-weight: 500;
  font-size: 13px;
  color: #67e8f9 !important;
  background: rgba(103, 232, 249, 0.06) !important;
  border-left: 2px solid rgba(103, 232, 249, 0.6);
  margin: 3px 4px 2px 8px;
  padding-left: 15px !important;
  border-radius: 6px;
}

:deep(.el-sub-menu .el-sub-menu > .el-sub-menu__title:hover) {
  background: rgba(103, 232, 249, 0.14) !important;
  border-left-color: #67e8f9;
  border-left-style: solid;
}

:deep(.el-sub-menu .el-sub-menu.is-opened > .el-sub-menu__title) {
  background: rgba(103, 232, 249, 0.1) !important;
  border-left-color: #67e8f9;
  border-left-style: solid;
}

/* 二级父目录下的子项列表 */
:deep(.el-sub-menu .el-sub-menu .el-sub-menu > .el-sub-menu__list) {
  padding-top: 3px;
  padding-bottom: 5px;
  border-bottom: none;
  margin-bottom: 0;
  background: rgba(0, 0, 0, 0.08);
  padding-left: 15px !important;
  border-radius: 0 0 6px 6px;
}

/* 三级父目录 - 淡琥珀色，与二级(青绿)区分 */
:deep(.el-sub-menu .el-sub-menu .el-sub-menu > .el-sub-menu__title) {
  font-weight: 500;
  font-size: 12.5px;
  color: #ffffff !important;
  background: rgba(253, 230, 138, 0.08) !important;
  border-left: 2px solid rgba(253, 230, 138, 0.6);
  margin: 2px 4px 2px 8px;
  padding-left: 25px !important;
  border-radius: 6px;
}

:deep(.el-sub-menu .el-sub-menu .el-sub-menu > .el-sub-menu__title:hover) {
  background: rgba(253, 230, 138, 0.16) !important;
  border-left-color: #fde68a;
  border-left-style: solid;
}

:deep(.el-sub-menu .el-sub-menu .el-sub-menu.is-opened > .el-sub-menu__title) {
  background: rgba(253, 230, 138, 0.12) !important;
  border-left-color: #fde68a;
  border-left-style: solid;
}

/* 三级父目录下的子项列表 */
:deep(.el-sub-menu .el-sub-menu .el-sub-menu .el-sub-menu > .el-sub-menu__list) {
  padding-top: 2px;
  padding-bottom: 4px;
  border-bottom: none;
  margin-bottom: 0;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 0 0 6px 6px;
}

/* ========== 叶子节点样式(最终可点击项)，颜色与所属层级一致 ========== */
/* 通用叶子节点基础样式 */
:deep(.el-menu-item) {
  height: 36px;
  line-height: 36px;
  margin: 2px 4px;
  border-radius: 6px;
  font-size: 13px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  width: auto;
  box-sizing: border-box;
  color: rgb(255, 255, 255);
}

/* 一级下的叶子(販売ホーム/生産ホーム/出荷構成表管理等) - 高亮白色 */
:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__list > .el-sub-menu > .el-sub-menu__list > .el-menu-item) {
  padding-left: 8px !important;
  font-size: 13px;
  color: #ffffff !important;
  margin-left: 4px;
}
:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__list > .el-sub-menu > .el-sub-menu__list > .el-menu-item .el-menu-tooltip__trigger) {
  padding-left: 8px !important;
}

/* 二级下的叶子(生産計画下的 生産データ管理等) - 高亮白色 */
:deep(.sidebar-el-menu .el-sub-menu .el-sub-menu .el-sub-menu .el-menu-item) {
  padding-left: 35px !important;
  font-size: 12.5px;
  color: #ffffff !important;
  margin-left: 8px;
}
:deep(.sidebar-el-menu .el-sub-menu .el-sub-menu .el-sub-menu .el-menu-item .el-menu-tooltip__trigger) {
  padding-left: 35px !important;
}

/* 三级下的叶子 - 高亮白色 */
:deep(.el-sub-menu .el-sub-menu .el-sub-menu .el-sub-menu .el-menu-item) {
  padding-left: 30px !important;
  font-size: 12px;
  color: #ffffff !important;
  margin-left: 8px;
}

:deep(.el-menu-item .el-menu-tooltip__trigger),
:deep(.el-menu-item > span) {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex !important;
  align-items: center !important;
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
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
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
  color: #a6ff00 !important;
}

/* 二级下的叶子(生産データ管理等) 悬停显示绿色 */
:deep(.sidebar-el-menu .el-sub-menu .el-sub-menu .el-sub-menu .el-menu-item:hover),
:deep(.sidebar-el-menu .el-sub-menu .el-sub-menu .el-sub-menu .el-menu-item:hover .el-menu-tooltip__trigger) {
  color: #55fc02 !important;
}

:deep(.el-sub-menu) {
  width: 100%;
}

/* Collapsed state：图标在上、短标签在下（与 Android SidebarMenu 一致） */
:deep(.sidebar-el-menu.el-menu--collapse) {
  width: 100% !important;
  padding: 4px 4px !important;
  box-sizing: border-box;
  --el-menu-base-level-padding: 0 !important;
  --el-menu-level-padding: 0 !important;
}

:deep(.sidebar-el-menu.el-menu--collapse .el-sub-menu) {
  padding-left: 0 !important;
  padding-right: 0 !important;
  padding-inline-start: 0 !important;
  padding-inline-end: 0 !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  width: 100% !important;
  max-width: none !important;
}

/* 折叠时顶级行：为图标+短标签留出高度 */
:deep(.sidebar-el-menu.el-menu--collapse > .el-menu-item),
:deep(.sidebar-el-menu.el-menu--collapse > .el-sub-menu > .el-sub-menu__title) {
  margin: 4px 0 !important;
  padding: 6px 2px !important;
  justify-content: center !important;
  align-items: center !important;
  min-height: 52px;
  height: auto !important;
  box-sizing: border-box;
  width: 100% !important;
  max-width: none !important;
  display: flex !important;
  overflow: visible !important;
}

/* 折叠时嵌套子菜单（非侧栏可见项）保持横向布局 */
:deep(.sidebar-el-menu.el-menu--collapse .el-sub-menu .el-sub-menu > .el-sub-menu__title),
:deep(.sidebar-el-menu.el-menu--collapse .el-sub-menu .el-menu-item) {
  margin: 2px 0 !important;
  padding: 0 !important;
  justify-content: center !important;
  min-height: 40px;
  height: 40px;
  box-sizing: border-box;
  width: 100% !important;
  max-width: none !important;
  display: flex !important;
  align-items: center !important;
  flex-direction: row !important;
}
:deep(.sidebar-el-menu.el-menu--collapse > .el-menu-item.menu-item-top),
:deep(.sidebar-el-menu.el-menu--collapse > .el-sub-menu > .el-sub-menu__title),
:deep(.sidebar-el-menu.el-menu--collapse .el-sub-menu .el-sub-menu > .el-sub-menu__title) {
  padding: 0 !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  border-left: none !important;
  background: transparent !important;
  border-radius: 8px !important;
  width: 100% !important;
  box-shadow: none !important;
}
/* 覆盖 Element Plus 折叠态 tooltip 触发器（默认 absolute + height:100% 会裁切下方文字） */
:deep(.sidebar-el-menu.el-menu--collapse > .el-menu-item) {
  position: relative !important;
  white-space: normal !important;
}

:deep(.sidebar-el-menu.el-menu--collapse > .el-menu-item .el-menu-tooltip__trigger) {
  position: relative !important;
  left: auto !important;
  top: auto !important;
  justify-content: center !important;
  align-items: center !important;
  padding: 0 !important;
  flex: none !important;
  width: 100% !important;
  min-width: 0 !important;
  height: auto !important;
  overflow: visible !important;
}

:deep(.sidebar-el-menu.el-menu--collapse > .el-sub-menu > .el-sub-menu__title) {
  line-height: normal !important;
  white-space: normal !important;
}

:deep(.sidebar-el-menu.el-menu--collapse .sidebar-collapsed-entry__label) {
  height: auto !important;
  width: auto !important;
  max-width: 100% !important;
  overflow: visible !important;
  visibility: visible !important;
  display: block !important;
}

:deep(.el-menu--collapse .el-sub-menu__icon-arrow) {
  display: none !important;
}

:deep(.sidebar-el-menu.el-menu--collapse .sidebar-collapsed-entry.is-collapsed .el-icon),
:deep(.el-menu--collapse .el-menu-item .el-icon),
:deep(.el-menu--collapse .el-sub-menu__title .el-icon) {
  margin-right: 0 !important;
  margin-left: 0 !important;
}

:deep(.sidebar-el-menu.el-menu--collapse > .el-sub-menu > .el-sub-menu__title .sidebar-collapsed-entry) {
  width: 100%;
}

/* 折叠时子菜单标题整行占满并居中图标（覆盖 Element 可能的内联/变量缩进） */
:deep(.sidebar-el-menu.el-menu--collapse .el-sub-menu .el-sub-menu__title) {
  padding-left: 0 !important;
  padding-right: 0 !important;
  padding-inline-start: 0 !important;
  padding-inline-end: 0 !important;
  width: 100% !important;
  min-width: 0 !important;
  justify-content: center !important;
  text-align: center !important;
}
:deep(.sidebar-el-menu.el-menu--collapse .el-sub-menu .el-sub-menu__title .el-icon) {
  margin: 0 !important;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.08) 100%);
  color: rgba(255, 254, 254, 0.7);
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

/* 带「ホーム」的弹出菜单项 - 橘黄色（含选中态） */
.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-menu-item.menu-item-home,
.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-menu-item.menu-item-home .el-menu-tooltip__trigger,
.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-menu-item.menu-item-home.is-active,
.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-menu-item.menu-item-home.is-active .el-menu-tooltip__trigger {
  color: #f8f66b !important;
  font-weight: 700 !important;
}
.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu .el-menu .el-menu-item.menu-item-home,
.el-menu--vertical.el-menu--popup-container .el-menu--popup .el-sub-menu .el-menu .el-menu-item.menu-item-home.is-active {
  color: #f8f66b !important;
  font-weight: 700 !important;
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
