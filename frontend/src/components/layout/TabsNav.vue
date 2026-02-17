<template>
  <div class="tabs-nav">
    <!-- 左箭头：内容超出时显示 -->
    <button
      v-show="canScrollLeft"
      type="button"
      class="nav-arrow nav-arrow--left"
      aria-label="左へスクロール"
      @click="scrollBy(-scrollStep)"
    >
      <el-icon :size="14"><ArrowLeft /></el-icon>
    </button>

    <div ref="scrollContainerRef" class="tabs-scroll" @scroll="updateScrollState">
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
    </div>

    <!-- 右箭头：内容超出时显示 -->
    <button
      v-show="canScrollRight"
      type="button"
      class="nav-arrow nav-arrow--right"
      aria-label="右へスクロール"
      @click="scrollBy(scrollStep)"
    >
      <el-icon :size="14"><ArrowRight /></el-icon>
    </button>
    
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
import { reactive, ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTabsStore, type TabItem } from '@/stores/tabs'
import { menuConfig } from '@/router/menuConfig'
import { Close, ArrowDown, Refresh, FolderRemove, DArrowLeft, DArrowRight, HomeFilled, Document, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

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

// 左右箭头滚动
const scrollContainerRef = ref<HTMLElement | null>(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)
const scrollStep = 180

function updateScrollState() {
  const el = scrollContainerRef.value
  if (!el) return
  const { scrollLeft, clientWidth, scrollWidth } = el
  canScrollLeft.value = scrollLeft > 2
  canScrollRight.value = scrollLeft + clientWidth < scrollWidth - 2
}

function scrollBy(delta: number) {
  const el = scrollContainerRef.value
  if (!el) return
  el.scrollLeft += delta
  nextTick(updateScrollState)
}

watch(() => tabsStore.tabs.length, () => {
  nextTick(updateScrollState)
})

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  document.addEventListener('click', closeContextMenu)
  nextTick(() => {
    const el = scrollContainerRef.value
    if (el) {
      updateScrollState()
      resizeObserver = new ResizeObserver(() => updateScrollState())
      resizeObserver.observe(el)
    }
  })
})

onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu)
  if (scrollContainerRef.value && resizeObserver) {
    resizeObserver.disconnect()
  }
})
</script>

<style scoped>
.tabs-nav {
  display: flex;
  align-items: center;
  height: 32px;
  min-height: 32px;
  background: linear-gradient(180deg,
    rgba(255, 255, 255, 0.97) 0%,
    rgba(248, 250, 252, 0.96) 100%
  );
  backdrop-filter: blur(6px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.55);
  padding: 0 6px;
  gap: 2px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  position: relative;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
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
    rgba(99, 102, 241, 0.08) 50%,
    transparent 100%
  );
  pointer-events: none;
}

/* 左右箭头 */
.nav-arrow {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  border-radius: 5px;
  background: rgba(248, 250, 252, 0.9);
  color: #64748b;
  cursor: pointer;
  transition: all 0.18s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.nav-arrow:hover {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  box-shadow: 0 1px 3px rgba(99, 102, 241, 0.12);
}

.nav-arrow:active {
  transform: scale(0.96);
}

.tabs-scroll {
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-behavior: smooth;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.tabs-scroll::-webkit-scrollbar {
  display: none;
}

.tabs-wrapper {
  display: flex;
  gap: 4px;
  padding: 4px 2px;
  width: max-content;
  min-width: 100%;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  background: linear-gradient(135deg,
    rgba(255, 255, 255, 0.92) 0%,
    rgba(248, 250, 252, 0.88) 100%
  );
  border: 1px solid rgba(226, 232, 240, 0.5);
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03),
              inset 0 1px 0 rgba(255, 255, 255, 0.85);
  flex-shrink: 0;
}

.tab-item::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 6px;
  background: linear-gradient(135deg,
    rgba(99, 102, 241, 0.04) 0%,
    rgba(139, 92, 246, 0.02) 100%
  );
  opacity: 0;
  transition: opacity 0.2s ease;
}

.tab-item:hover {
  border-color: rgba(99, 102, 241, 0.28);
  color: #334155;
  background: linear-gradient(135deg,
    rgba(255, 255, 255, 0.98) 0%,
    rgba(248, 250, 252, 0.95) 100%
  );
  box-shadow: 0 1px 4px rgba(99, 102, 241, 0.08),
              0 1px 2px rgba(0, 0, 0, 0.03),
              inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.tab-item:hover::after {
  opacity: 1;
}

.tab-item.is-active {
  background: linear-gradient(135deg,
    #6366f1 0%,
    #7c3aed 100%
  );
  border-color: transparent;
  color: #fff;
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.35),
              0 1px 2px rgba(99, 102, 241, 0.2),
              inset 0 1px 0 rgba(255, 255, 255, 0.18);
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
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  letter-spacing: 0.02em;
  line-height: 1.25;
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
  padding-left: 6px;
  margin-left: 2px;
  border-left: 1px solid rgba(226, 232, 240, 0.45);
  flex-shrink: 0;
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
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.5);
  transition: all 0.18s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.action-btn:hover {
  color: #6366f1;
  border-color: rgba(99, 102, 241, 0.35);
  background: rgba(99, 102, 241, 0.08);
  box-shadow: 0 1px 3px rgba(99, 102, 241, 0.12);
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
  color: #6366f1;
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
  color: #6366f1;
}

:deep(.el-dropdown-menu__item .el-icon) {
  font-size: 14px;
  color: #6366f1;
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
    height: 30px;
    padding: 0 4px;
    gap: 1px;
  }

  .nav-arrow {
    width: 22px;
    height: 22px;
  }

  .nav-arrow .el-icon {
    font-size: 12px;
  }

  .tab-title {
    max-width: 72px;
  }

  .tab-item {
    padding: 3px 8px;
    font-size: 11px;
    gap: 4px;
  }

  .tabs-wrapper {
    padding: 3px 2px;
  }

  .action-btn {
    width: 22px;
    height: 22px;
  }
}
</style>
