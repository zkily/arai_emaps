<template>
  <div class="sidebar-menu sbm-lite">
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
      <!-- サブメニューは常にポップアップ表示（collapse=true）。サイドバーの開閉は is-sb-collapsed で切り替える -->
      <el-menu
        :default-active="activeMenu"
        :collapse="true"
        :collapse-transition="false"
        :show-timeout="60"
        :hide-timeout="180"
        :popper-offset="10"
        class="sidebar-el-menu"
        :class="{ 'is-sb-collapsed': isCollapsed }"
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

        <SidebarShortcutsSection :is-collapsed="isCollapsed" class="sb-root sb-root--shortcuts" />

        <MenuTreeItem
          v-for="section in visibleRootMenus"
          :key="section.code"
          :node="section"
          :is-collapsed="isCollapsed"
          :class="`sb-root sb-root--${section.code.toLowerCase()}`"
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
import SidebarShortcutsSection from '@/components/layout/SidebarShortcutsSection.vue'
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
  background:
    radial-gradient(120% 36% at 0% 0%, rgba(99, 102, 241, 0.2) 0%, transparent 60%),
    linear-gradient(180deg, #171b36 0%, #222847 50%, #181c37 100%);
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.06);
}

/* ---------- Logo ---------- */
.logo {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  /* HeaderBar の高さ（48px / 768px 以下 46px）と揃える */
  height: 48px;
  flex-shrink: 0;
  gap: 10px;
  cursor: pointer;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.15) 100%);
  transition: background-color 0.2s ease;
}

.logo::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  background: linear-gradient(90deg, #a855f7, #f43f5e, #06b6d4, #f59e0b, #10b981, #60a5fa);
  opacity: 0.7;
  pointer-events: none;
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
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.logo-image {
  height: 40px;
  width: auto;
  object-fit: contain;
}

.logo-favicon {
  width: 22px;
  height: 22px;
  object-fit: contain;
}

.menu-scrollbar {
  flex: 1;
  overflow: hidden;
}

/* ---------- ルート行（ダッシュボード・よく使う・各モジュール） ---------- */
:deep(.sidebar-el-menu) {
  --sc: #a5b4fc;
  --sc-rgb: 165, 180, 252;
  width: 100% !important;
  padding: 8px 8px 10px;
  border-right: none;
  box-sizing: border-box;
}

:deep(.sidebar-el-menu .sb-root--shortcuts) {
  --sc: #fb923c;
  --sc-rgb: 251, 146, 60;
}
:deep(.sidebar-el-menu .sb-root--erp) {
  --sc: #c084fc;
  --sc-rgb: 192, 132, 252;
}
:deep(.sidebar-el-menu .sb-root--aps) {
  --sc: #fb7185;
  --sc-rgb: 251, 113, 133;
}
:deep(.sidebar-el-menu .sb-root--mes) {
  --sc: #22d3ee;
  --sc-rgb: 34, 211, 238;
}
:deep(.sidebar-el-menu .sb-root--fin) {
  --sc: #fbbf24;
  --sc-rgb: 251, 191, 36;
}
:deep(.sidebar-el-menu .sb-root--master) {
  --sc: #34d399;
  --sc-rgb: 52, 211, 153;
}
:deep(.sidebar-el-menu .sb-root--system) {
  --sc: #60a5fa;
  --sc-rgb: 96, 165, 250;
}

:deep(.sidebar-el-menu > .el-menu-item),
:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__title) {
  position: relative;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  height: 42px !important;
  line-height: 42px !important;
  margin: 3px 0 !important;
  padding: 0 30px 0 8px !important;
  border: none !important;
  border-radius: 11px !important;
  font-size: 13.5px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.86) !important;
  background: transparent !important;
  box-shadow: none !important;
  transition:
    background-color 0.18s ease,
    color 0.18s ease,
    box-shadow 0.18s ease !important;
}

:deep(.sidebar-el-menu > .el-menu-item)::before,
:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__title)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  width: 3px;
  height: 0;
  border-radius: 0 3px 3px 0;
  background: var(--sc);
  transform: translateY(-50%);
  transition: height 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}

:deep(.sidebar-el-menu .sidebar-collapsed-entry) {
  gap: 10px;
}

:deep(.sidebar-el-menu > .el-menu-item .sidebar-collapsed-entry > .el-icon),
:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__title .sidebar-collapsed-entry > .el-icon) {
  flex-shrink: 0;
  width: 30px !important;
  height: 30px;
  margin: 0 !important;
  border-radius: 9px;
  font-size: 16px;
  color: var(--sc);
  background: rgba(var(--sc-rgb), 0.14);
  box-shadow: inset 0 0 0 1px rgba(var(--sc-rgb), 0.22);
  transition:
    background-color 0.18s ease,
    color 0.18s ease,
    box-shadow 0.18s ease;
}

:deep(.sidebar-el-menu .sidebar-collapsed-entry__title) {
  line-height: 1.6;
}

/* 右端の矢印（ポップアップ方向） */
:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__title .el-sub-menu__icon-arrow) {
  position: absolute !important;
  right: 10px !important;
  top: 50% !important;
  display: inline-flex !important;
  margin: -6px 0 0 !important;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  transform: none !important;
  transition:
    transform 0.2s cubic-bezier(0.22, 1, 0.36, 1),
    color 0.18s ease !important;
}

:deep(.sidebar-el-menu > .el-menu-item:hover),
:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__title:hover) {
  color: #fff !important;
  background: rgba(var(--sc-rgb), 0.12) !important;
}

:deep(.sidebar-el-menu > .el-menu-item:hover .sidebar-collapsed-entry > .el-icon),
:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__title:hover .sidebar-collapsed-entry > .el-icon) {
  background: rgba(var(--sc-rgb), 0.24);
}

:deep(.sidebar-el-menu > .el-sub-menu > .el-sub-menu__title:hover .el-sub-menu__icon-arrow),
:deep(.sidebar-el-menu > .el-sub-menu.is-opened > .el-sub-menu__title .el-sub-menu__icon-arrow) {
  color: var(--sc);
  transform: translateX(3px) !important;
}

/* ポップアップ表示中 */
:deep(.sidebar-el-menu > .el-sub-menu.is-opened > .el-sub-menu__title) {
  color: #fff !important;
  background: linear-gradient(90deg, rgba(var(--sc-rgb), 0.26) 0%, rgba(var(--sc-rgb), 0.08) 100%) !important;
}

:deep(.sidebar-el-menu > .el-sub-menu.is-opened > .el-sub-menu__title)::before,
:deep(.sidebar-el-menu > .el-sub-menu.is-active > .el-sub-menu__title)::before,
:deep(.sidebar-el-menu > .el-menu-item.is-active)::before {
  height: 22px;
}

/* 現在のページを含むモジュール */
:deep(.sidebar-el-menu > .el-sub-menu.is-active > .el-sub-menu__title),
:deep(.sidebar-el-menu > .el-menu-item.is-active) {
  color: #fff !important;
}

:deep(.sidebar-el-menu > .el-sub-menu.is-active > .el-sub-menu__title .sidebar-collapsed-entry > .el-icon),
:deep(.sidebar-el-menu > .el-menu-item.is-active .sidebar-collapsed-entry > .el-icon) {
  color: #fff;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 55%),
    rgb(var(--sc-rgb));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 -2px 0 rgba(0, 0, 0, 0.18),
    0 4px 10px -4px rgba(var(--sc-rgb), 0.7);
}

:deep(.sidebar-el-menu > .el-menu-item.is-active) {
  background: rgba(var(--sc-rgb), 0.12) !important;
}

/* ---------- 折りたたみ時：アイコン + 短縮ラベル ---------- */
:deep(.sidebar-el-menu.is-sb-collapsed) {
  padding: 8px 6px 10px;
}

:deep(.sidebar-el-menu.is-sb-collapsed > .el-menu-item),
:deep(.sidebar-el-menu.is-sb-collapsed > .el-sub-menu > .el-sub-menu__title) {
  justify-content: center !important;
  height: auto !important;
  min-height: 56px;
  line-height: normal !important;
  padding: 6px 2px !important;
  white-space: normal !important;
}

:deep(.sidebar-el-menu.is-sb-collapsed > .el-sub-menu > .el-sub-menu__title .el-sub-menu__icon-arrow) {
  display: none !important;
}

:deep(.sidebar-el-menu.is-sb-collapsed .sidebar-collapsed-entry) {
  gap: 4px;
}

:deep(.sidebar-el-menu.is-sb-collapsed .sidebar-collapsed-entry__label) {
  display: block !important;
  width: auto !important;
  height: auto !important;
  max-width: 100% !important;
  overflow: hidden !important;
  visibility: visible !important;
  color: rgba(255, 255, 255, 0.78);
}

:deep(.sidebar-el-menu.is-sb-collapsed > .el-sub-menu.is-active .sidebar-collapsed-entry__label),
:deep(.sidebar-el-menu.is-sb-collapsed > .el-menu-item.is-active .sidebar-collapsed-entry__label),
:deep(.sidebar-el-menu.is-sb-collapsed > .el-sub-menu.is-opened .sidebar-collapsed-entry__label) {
  color: #fff;
}

/* ---------- 折りたたみボタン ---------- */
.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  flex-shrink: 0;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.7);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.08) 100%);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  transition:
    background-color 0.2s ease,
    color 0.2s ease;
}

.collapse-btn:hover {
  color: #fff;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.15) 100%);
}

.collapse-text {
  font-size: 12px;
  font-weight: 500;
}

.fade-text-enter-active,
.fade-text-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.fade-text-enter-from,
.fade-text-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}

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

@media (max-width: 768px) {
  .logo {
    height: 46px;
  }
}
</style>

<!-- サブメニューのポップアップ（body へ teleport されるためグローバル指定） -->
<style>
.sbm-popper {
  --sc: #a5b4fc;
  --sc-rgb: 165, 180, 252;
}
.sbm-popper.sbm-popper--shortcuts {
  --sc: #fb923c;
  --sc-rgb: 251, 146, 60;
}
.sbm-popper.sbm-popper--erp {
  --sc: #c084fc;
  --sc-rgb: 192, 132, 252;
}
.sbm-popper.sbm-popper--aps {
  --sc: #fb7185;
  --sc-rgb: 251, 113, 133;
}
.sbm-popper.sbm-popper--mes {
  --sc: #22d3ee;
  --sc-rgb: 34, 211, 238;
}
.sbm-popper.sbm-popper--fin {
  --sc: #fbbf24;
  --sc-rgb: 251, 191, 36;
}
.sbm-popper.sbm-popper--master {
  --sc: #34d399;
  --sc-rgb: 52, 211, 153;
}
.sbm-popper.sbm-popper--system {
  --sc: #60a5fa;
  --sc-rgb: 96, 165, 250;
}

.el-popper.sbm-popper {
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
}

/* 開閉アニメーション：横スライド + フェード */
.el-popper.sbm-popper.el-zoom-in-left-enter-active {
  opacity: 1;
  transform: none;
  transform-origin: left top;
  transition:
    opacity 0.16s ease-out,
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}
.el-popper.sbm-popper.el-zoom-in-left-leave-active {
  opacity: 0;
  transform: translateX(-4px);
  transition:
    opacity 0.12s ease-in,
    transform 0.12s ease-in;
}
.el-popper.sbm-popper.el-zoom-in-left-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}

.sbm-popper .el-menu--popup {
  min-width: 212px !important;
  max-width: 300px;
  max-height: calc(100vh - 24px);
  overflow-y: auto;
  padding: 6px !important;
  border: 1px solid rgba(var(--sc-rgb), 0.26) !important;
  border-top: 3px solid var(--sc) !important;
  border-radius: 12px !important;
  background: linear-gradient(180deg, #252b4c 0%, #1b2040 100%) !important;
  box-shadow:
    0 16px 36px -12px rgba(4, 6, 22, 0.7),
    0 0 0 1px rgba(0, 0, 0, 0.18) !important;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
}

.sbm-popper .sbm-popup-head {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0 0 4px;
  padding: 4px 8px 7px;
  list-style: none;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  white-space: nowrap;
  color: var(--sc);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  cursor: default;
}

.sbm-popper .sbm-popup-head__dot {
  flex-shrink: 0;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--sc);
  box-shadow: 0 0 0 3px rgba(var(--sc-rgb), 0.22);
}

.sbm-popper .el-menu--popup .el-menu-item,
.sbm-popper .el-menu--popup .el-sub-menu__title {
  position: relative;
  display: flex !important;
  align-items: center !important;
  min-width: 0 !important;
  height: 34px !important;
  line-height: 34px !important;
  margin: 1px 0 !important;
  padding: 0 10px !important;
  border: none !important;
  border-radius: 8px !important;
  font-size: 12.5px !important;
  font-weight: 500;
  white-space: nowrap;
  color: rgba(226, 232, 240, 0.9) !important;
  background: transparent !important;
  box-shadow: none !important;
  transition:
    background-color 0.15s ease,
    color 0.15s ease !important;
}

.sbm-popper .el-menu--popup .el-sub-menu__title {
  padding-right: 28px !important;
  font-weight: 600;
}

.sbm-popper .el-menu--popup .el-menu-item > .el-icon,
.sbm-popper .el-menu--popup .el-sub-menu__title > .el-icon:not(.el-sub-menu__icon-arrow) {
  flex-shrink: 0;
  width: 16px !important;
  margin: 0 8px 0 0 !important;
  font-size: 15px;
  color: rgba(var(--sc-rgb), 0.85);
  transition: color 0.15s ease;
}

.sbm-popper .el-menu--popup .el-menu-item > span,
.sbm-popper .el-menu--popup .el-sub-menu__title > span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.6;
}

.sbm-popper .menu-tree-leaf__row {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  min-width: 0;
}

.sbm-popper .menu-tree-leaf__label {
  line-height: 1.6;
}

.sbm-popper .el-menu--popup .el-sub-menu__icon-arrow {
  position: absolute !important;
  right: 8px !important;
  top: 50% !important;
  margin: -6px 0 0 !important;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  transform: none !important;
  transition:
    transform 0.2s cubic-bezier(0.22, 1, 0.36, 1),
    color 0.15s ease !important;
}

.sbm-popper .el-menu--popup .el-menu-item:hover,
.sbm-popper .el-menu--popup .el-sub-menu__title:hover,
.sbm-popper .el-menu--popup .el-sub-menu.is-opened > .el-sub-menu__title {
  color: #fff !important;
  background: rgba(var(--sc-rgb), 0.16) !important;
}

.sbm-popper .el-menu--popup .el-menu-item:hover > .el-icon,
.sbm-popper .el-menu--popup .el-sub-menu__title:hover > .el-icon:not(.el-sub-menu__icon-arrow) {
  color: var(--sc);
}

.sbm-popper .el-menu--popup .el-sub-menu__title:hover .el-sub-menu__icon-arrow,
.sbm-popper .el-menu--popup .el-sub-menu.is-opened > .el-sub-menu__title .el-sub-menu__icon-arrow {
  color: var(--sc);
  transform: translateX(3px) !important;
}

.sbm-popper .el-menu--popup .el-sub-menu.is-active > .el-sub-menu__title {
  color: #fff !important;
  font-weight: 700;
  box-shadow: inset 3px 0 0 var(--sc) !important;
}

.sbm-popper .el-menu--popup .el-menu-item.is-active {
  color: #fff !important;
  font-weight: 700;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0) 60%),
    rgb(var(--sc-rgb)) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.25),
    inset 0 -2px 0 rgba(0, 0, 0, 0.18) !important;
}

.sbm-popper .el-menu--popup .el-menu-item.is-active > .el-icon {
  color: #fff;
}

.sbm-popper .el-menu--popup .el-menu-item.menu-item-home:not(.is-active) {
  color: #fde68a !important;
  font-weight: 700;
}

.sbm-popper .el-menu--popup .el-menu-item:hover .menu-tree-leaf__pin,
.sbm-popper .el-menu--popup .el-menu-item:hover .shortcut-remove {
  opacity: 1;
}

.sbm-popper .el-menu--popup .el-menu-item.is-active .menu-tree-leaf__pin:not(.is-pinned) {
  color: rgba(255, 255, 255, 0.75);
}

.sbm-popper .shortcut-item--pinned .shortcut-kind-icon {
  color: #fbbf24 !important;
}

.sbm-popper .shortcut-item--frequent .shortcut-kind-icon {
  color: #7dd3fc !important;
}

@media (prefers-reduced-motion: reduce) {
  .el-popper.sbm-popper.el-zoom-in-left-enter-active,
  .el-popper.sbm-popper.el-zoom-in-left-leave-active {
    transition: opacity 0.1s linear;
  }
  .el-popper.sbm-popper.el-zoom-in-left-enter-from,
  .el-popper.sbm-popper.el-zoom-in-left-leave-active {
    transform: none;
  }
}
</style>
