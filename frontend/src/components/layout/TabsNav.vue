<template>
  <div class="tabs-nav">
    <div class="tabs-scroll">
      <el-scrollbar>
        <div class="tabs-wrapper">
          <div
            v-for="tab in tabsStore.tabs"
            :key="tab.path"
            :class="['tab-item', { 'is-active': tab.path === tabsStore.activeTab }]"
            @click="handleTabClick(tab)"
            @contextmenu.prevent="handleContextMenu($event, tab)"
          >
            <el-icon class="tab-icon" :size="12">
              <HomeFilled v-if="tab.path === '/dashboard'" />
              <Document v-else />
            </el-icon>
            <span class="tab-title">{{ tabTitle(tab) }}</span>
            <el-icon
              v-if="tab.closable"
              class="tab-close"
              :size="11"
              @click.stop="handleClose(tab.path)"
            >
              <Close />
            </el-icon>
          </div>
        </div>
      </el-scrollbar>
    </div>
    
    <!-- 操作按钮 -->
    <div class="tabs-actions">
      <el-dropdown trigger="click" @command="handleCommand">
        <div class="action-btn">
          <el-icon :size="12"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="refresh">
              <el-icon><Refresh /></el-icon>
              {{ t('common.tabsRefresh') }}
            </el-dropdown-item>
            <el-dropdown-item command="closeOthers" divided>
              <el-icon><Close /></el-icon>
              {{ t('common.tabsCloseOthers') }}
            </el-dropdown-item>
            <el-dropdown-item command="closeAll">
              <el-icon><FolderRemove /></el-icon>
              {{ t('common.tabsCloseAll') }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
    
    <!-- 右键菜单 -->
    <teleport to="body">
      <transition name="context-menu-fade">
        <div
          v-if="contextMenu.visible"
          class="context-menu"
          :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        >
          <div class="context-menu-item" @click="handleContextMenuAction('refresh')">
            <el-icon><Refresh /></el-icon>
            <span>{{ t('common.tabsRefresh') }}</span>
          </div>
          <div class="context-menu-item" @click="handleContextMenuAction('close')" v-if="contextMenu.tab?.closable">
            <el-icon><Close /></el-icon>
            <span>{{ t('common.tabsClose') }}</span>
          </div>
          <div class="context-menu-divider"></div>
          <div class="context-menu-item" @click="handleContextMenuAction('closeOthers')">
            <el-icon><Close /></el-icon>
            <span>{{ t('common.tabsCloseOthers') }}</span>
          </div>
          <div class="context-menu-item" @click="handleContextMenuAction('closeLeft')">
            <el-icon><DArrowLeft /></el-icon>
            <span>{{ t('common.tabsCloseLeft') }}</span>
          </div>
          <div class="context-menu-item" @click="handleContextMenuAction('closeRight')">
            <el-icon><DArrowRight /></el-icon>
            <span>{{ t('common.tabsCloseRight') }}</span>
          </div>
          <div class="context-menu-divider"></div>
          <div class="context-menu-item context-menu-item--danger" @click="handleContextMenuAction('closeAll')">
            <el-icon><FolderRemove /></el-icon>
            <span>{{ t('common.tabsCloseAll') }}</span>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTabsStore, type TabItem } from '@/stores/tabs'
import { menuConfig } from '@/router/menuConfig'
import { Close, ArrowDown, Refresh, FolderRemove, DArrowLeft, DArrowRight, HomeFilled, Document } from '@element-plus/icons-vue'

const { t } = useI18n()
const router = useRouter()
const tabsStore = useTabsStore()

// Path to menu code for tab title translation
const pathToMenuCode = computed(() => {
  const map: Record<string, string> = { '/dashboard': 'DASHBOARD' }
  menuConfig.forEach((m) => {
    if (m.path) map[m.path] = m.code
  })
  return map
})
const tabTitle = (tab: TabItem) => {
  const code = pathToMenuCode.value[tab.path]
  return code ? t('menu.' + code) : tab.title
}

const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  tab: null as TabItem | null
})

const handleTabClick = (tab: TabItem) => {
  if (tab.path !== tabsStore.activeTab) {
    tabsStore.setActiveTab(tab.path)
    router.push({
      path: tab.path,
      query: tab.query ?? {},
    })
  }
}

const handleClose = (path: string) => {
  const nextPath = tabsStore.closeTab(path)
  if (nextPath) {
    router.push(nextPath)
  }
}

const handleCommand = (command: string) => {
  switch (command) {
    case 'refresh':
      tabsStore.refreshTab(tabsStore.activeTab)
      const currentPath = tabsStore.activeTab
      router.replace({ path: '/redirect' + currentPath })
      break
    case 'closeOthers':
      tabsStore.closeOtherTabs(tabsStore.activeTab)
      break
    case 'closeAll':
      const path = tabsStore.closeAllTabs()
      router.push(path)
      break
  }
}

const handleContextMenu = (event: MouseEvent, tab: TabItem) => {
  contextMenu.visible = true
  contextMenu.x = event.clientX
  contextMenu.y = event.clientY
  contextMenu.tab = tab
}

const handleContextMenuAction = (action: string) => {
  if (!contextMenu.tab) return
  
  const tabPath = contextMenu.tab.path
  
  switch (action) {
    case 'refresh':
      tabsStore.refreshTab(tabPath)
      if (tabPath === tabsStore.activeTab) {
        router.replace({ path: '/redirect' + tabPath })
      }
      break
    case 'close':
      const nextPath = tabsStore.closeTab(tabPath)
      if (nextPath) {
        router.push(nextPath)
      }
      break
    case 'closeOthers':
      tabsStore.closeOtherTabs(tabPath)
      tabsStore.setActiveTab(tabPath)
      router.push(tabPath)
      break
    case 'closeLeft':
      tabsStore.closeLeftTabs(tabPath)
      break
    case 'closeRight':
      tabsStore.closeRightTabs(tabPath)
      break
    case 'closeAll':
      const path = tabsStore.closeAllTabs()
      router.push(path)
      break
  }
  
  contextMenu.visible = false
}

const closeContextMenu = () => {
  contextMenu.visible = false
}

onMounted(() => {
  document.addEventListener('click', closeContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu)
})
</script>

<style scoped>
.tabs-nav {
  display: flex;
  align-items: center;
  height: 32px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  padding: 0 6px;
}

.tabs-scroll {
  flex: 1;
  overflow: hidden;
}

.tabs-wrapper {
  display: flex;
  gap: 3px;
  padding: 3px 0;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 5px;
  cursor: pointer;
  white-space: nowrap;
  font-size: 11px;
  color: #64748b;
  transition: all 0.18s ease;
  position: relative;
}

.tab-item::before {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 2px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px 2px 0 0;
  transition: width 0.2s ease;
}

.tab-item:hover {
  border-color: #cbd5e1;
  color: #334155;
  background: #f8fafc;
}

.tab-item:hover::before {
  width: 60%;
}

.tab-item.is-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: white;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

.tab-item.is-active::before {
  display: none;
}

.tab-icon {
  opacity: 0.6;
  flex-shrink: 0;
}

.tab-item:hover .tab-icon {
  opacity: 0.85;
}

.tab-item.is-active .tab-icon {
  opacity: 1;
  color: white;
}

.tab-title {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

.tab-close {
  opacity: 0;
  padding: 2px;
  border-radius: 3px;
  transition: all 0.15s ease;
  margin-left: 2px;
  flex-shrink: 0;
}

.tab-item:hover .tab-close {
  opacity: 0.6;
}

.tab-close:hover {
  opacity: 1 !important;
  background: rgba(0, 0, 0, 0.08);
}

.tab-item.is-active .tab-close {
  opacity: 0.7;
  color: white;
}

.tab-item.is-active .tab-close:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.2);
}

.tabs-actions {
  display: flex;
  align-items: center;
  padding-left: 6px;
  margin-left: 3px;
  border-left: 1px solid #e2e8f0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 5px;
  cursor: pointer;
  color: #64748b;
  background: white;
  border: 1px solid #e2e8f0;
  transition: all 0.18s ease;
}

.action-btn:hover {
  color: #667eea;
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.05) 100%);
}

/* Context Menu */
.context-menu {
  position: fixed;
  z-index: 9999;
  background: white;
  border-radius: 8px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 4px;
  min-width: 150px;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  cursor: pointer;
  font-size: 11px;
  color: #334155;
  border-radius: 5px;
  transition: all 0.15s ease;
}

.context-menu-item:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.06) 100%);
  color: #667eea;
}

.context-menu-item .el-icon {
  font-size: 13px;
  opacity: 0.7;
}

.context-menu-item:hover .el-icon {
  opacity: 1;
}

.context-menu-item--danger:hover {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.06) 100%);
  color: #dc2626;
}

.context-menu-divider {
  height: 1px;
  background: #e2e8f0;
  margin: 3px 6px;
}

/* Animation */
.context-menu-fade-enter-active,
.context-menu-fade-leave-active {
  transition: all 0.15s ease;
}

.context-menu-fade-enter-from,
.context-menu-fade-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-4px);
}

/* Scrollbar */
:deep(.el-scrollbar__bar) {
  display: none;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  padding: 7px 12px;
}

:deep(.el-dropdown-menu__item .el-icon) {
  font-size: 13px;
  color: #667eea;
}

/* Responsive */
@media (max-width: 768px) {
  .tabs-nav {
    height: 30px;
    padding: 0 4px;
  }
  
  .tab-title {
    max-width: 50px;
  }
  
  .tab-item {
    padding: 2px 6px;
    font-size: 10px;
  }
}
</style>
