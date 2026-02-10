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
  height: 38px;
  background: linear-gradient(180deg, 
    rgba(255, 255, 255, 0.95) 0%, 
    rgba(248, 250, 252, 0.98) 50%,
    rgba(241, 245, 249, 0.95) 100%
  );
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  padding: 0 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02), 
              0 1px 2px rgba(0, 0, 0, 0.03);
  position: relative;
}

.tabs-nav::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(102, 126, 234, 0.1) 50%, 
    transparent 100%
  );
}

.tabs-scroll {
  flex: 1;
  overflow: hidden;
}

.tabs-wrapper {
  display: flex;
  gap: 6px;
  padding: 5px 0;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.9) 0%, 
    rgba(248, 250, 252, 0.85) 100%
  );
  border: 1px solid rgba(226, 232, 240, 0.5);
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  font-size: 12px;
  color: #64748b;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03),
              inset 0 1px 1px rgba(255, 255, 255, 0.8);
}

.tab-item::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 8px;
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.03) 0%, 
    rgba(118, 75, 162, 0.02) 100%
  );
  opacity: 0;
  transition: opacity 0.25s ease;
}

.tab-item:hover {
  border-color: rgba(102, 126, 234, 0.3);
  color: #475569;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.95) 0%, 
    rgba(248, 250, 252, 0.9) 100%
  );
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.08),
              0 1px 2px rgba(0, 0, 0, 0.04),
              inset 0 1px 1px rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

.tab-item:hover::after {
  opacity: 1;
}

.tab-item.is-active {
  background: linear-gradient(135deg, 
    #667eea 0%, 
    #764ba2 100%
  );
  border-color: transparent;
  color: white;
  box-shadow: 0 3px 8px rgba(102, 126, 234, 0.35),
              0 1px 3px rgba(102, 126, 234, 0.25),
              inset 0 1px 1px rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.tab-item.is-active::after {
  display: none;
}

.tab-icon {
  opacity: 0.65;
  flex-shrink: 0;
  transition: all 0.25s ease;
}

.tab-item:hover .tab-icon {
  opacity: 0.9;
  transform: scale(1.05);
}

.tab-item.is-active .tab-icon {
  opacity: 1;
  color: white;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.15));
}

.tab-title {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  letter-spacing: 0.01em;
}

.tab-close {
  opacity: 0;
  padding: 2px;
  border-radius: 4px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-left: 2px;
  flex-shrink: 0;
}

.tab-item:hover .tab-close {
  opacity: 0.6;
}

.tab-close:hover {
  opacity: 1 !important;
  background: rgba(0, 0, 0, 0.1);
  transform: scale(1.1);
}

.tab-item.is-active .tab-close {
  opacity: 0.75;
  color: white;
}

.tab-item.is-active .tab-close:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.1);
}

.tabs-actions {
  display: flex;
  align-items: center;
  padding-left: 10px;
  margin-left: 6px;
  border-left: 1px solid rgba(226, 232, 240, 0.5);
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  cursor: pointer;
  color: #64748b;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.9) 0%, 
    rgba(248, 250, 252, 0.85) 100%
  );
  border: 1px solid rgba(226, 232, 240, 0.5);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03),
              inset 0 1px 1px rgba(255, 255, 255, 0.8);
}

.action-btn:hover {
  color: #667eea;
  border-color: rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.12) 0%, 
    rgba(118, 75, 162, 0.08) 100%
  );
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.15),
              0 1px 2px rgba(0, 0, 0, 0.05),
              inset 0 1px 1px rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

/* Context Menu */
.context-menu {
  position: fixed;
  z-index: 9999;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.98) 0%, 
    rgba(248, 250, 252, 0.95) 100%
  );
  backdrop-filter: blur(12px);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 
              0 4px 16px rgba(0, 0, 0, 0.08),
              0 0 0 1px rgba(0, 0, 0, 0.04);
  padding: 6px;
  min-width: 160px;
  border: 1px solid rgba(226, 232, 240, 0.6);
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 12px;
  color: #475569;
  border-radius: 6px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  letter-spacing: 0.01em;
}

.context-menu-item:hover {
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.12) 0%, 
    rgba(118, 75, 162, 0.08) 100%
  );
  color: #667eea;
  box-shadow: 0 1px 3px rgba(102, 126, 234, 0.1);
  transform: translateX(2px);
}

.context-menu-item .el-icon {
  font-size: 14px;
  opacity: 0.75;
  transition: all 0.2s ease;
}

.context-menu-item:hover .el-icon {
  opacity: 1;
  transform: scale(1.1);
}

.context-menu-item--danger:hover {
  background: linear-gradient(135deg, 
    rgba(239, 68, 68, 0.12) 0%, 
    rgba(220, 38, 38, 0.08) 100%
  );
  color: #dc2626;
  box-shadow: 0 1px 3px rgba(239, 68, 68, 0.15);
}

.context-menu-divider {
  height: 1px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(226, 232, 240, 0.8) 50%,
    transparent 100%
  );
  margin: 4px 8px;
}

/* Animation */
.context-menu-fade-enter-active,
.context-menu-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.context-menu-fade-enter-from,
.context-menu-fade-leave-to {
  opacity: 0;
  transform: scale(0.92) translateY(-8px);
}

/* Scrollbar */
:deep(.el-scrollbar__bar) {
  display: none;
}

:deep(.el-dropdown-menu) {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.98) 0%, 
    rgba(248, 250, 252, 0.95) 100%
  );
  backdrop-filter: blur(12px);
  border: 1px solid rgba(226, 232, 240, 0.6);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 
              0 4px 16px rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  padding: 6px;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.el-dropdown-menu__item:hover) {
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.12) 0%, 
    rgba(118, 75, 162, 0.08) 100%
  );
  color: #667eea;
}

:deep(.el-dropdown-menu__item .el-icon) {
  font-size: 14px;
  color: #667eea;
  opacity: 0.85;
  transition: all 0.2s ease;
}

:deep(.el-dropdown-menu__item:hover .el-icon) {
  opacity: 1;
  transform: scale(1.1);
}

/* Responsive */
@media (max-width: 768px) {
  .tabs-nav {
    height: 34px;
    padding: 0 8px;
  }
  
  .tab-title {
    max-width: 60px;
  }
  
  .tab-item {
    padding: 4px 8px;
    font-size: 11px;
    gap: 4px;
  }
  
  .action-btn {
    width: 24px;
    height: 24px;
  }
}
</style>
