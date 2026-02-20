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
  --tabs-ease: cubic-bezier(0.34, 1.56, 0.64, 1);
  --tabs-ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  display: flex;
  align-items: center;
  height: 36px;
  min-height: 36px;
  background: linear-gradient(180deg,
    #ffffff 0%,
    #fafbfc 50%,
    #f8fafc 100%
  );
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(203, 213, 225, 0.8);
  padding: 0 8px;
  gap: 4px;
  box-shadow:
    0 1px 0 0 rgba(255, 255, 255, 0.9) inset,
    0 2px 8px rgba(0, 0, 0, 0.04);
  position: relative;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
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
    rgba(99, 102, 241, 0.12) 20%,
    rgba(99, 102, 241, 0.18) 50%,
    rgba(99, 102, 241, 0.12) 80%,
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
  width: 26px;
  height: 26px;
  padding: 0;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 6px;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
  color: #64748b;
  cursor: pointer;
  transition: transform 0.2s var(--tabs-ease-out), color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.nav-arrow:hover {
  color: #6366f1;
  border-color: rgba(99, 102, 241, 0.35);
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.15);
  transform: scale(1.05);
}

.nav-arrow:active {
  transform: scale(0.95);
  transition-duration: 0.1s;
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
  gap: 6px;
  padding: 5px 4px;
  width: max-content;
  min-width: 100%;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: linear-gradient(180deg,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(248, 250, 252, 0.92) 100%
  );
  border: 1px solid rgba(226, 232, 240, 0.7);
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
  color: #20242b;
  transition: color 0.2s ease, border-color 0.25s var(--tabs-ease-out), box-shadow 0.25s var(--tabs-ease-out),
    background 0.25s var(--tabs-ease-out), transform 0.2s var(--tabs-ease-out);
  position: relative;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  flex-shrink: 0;
}

.tab-item::before {
  content: '';
  position: absolute;
  bottom: 3px;
  left: 50%;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 1px;
  transition: width 0.3s var(--tabs-ease), left 0.3s var(--tabs-ease);
}

.tab-item::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.06) 0%, rgba(139, 92, 246, 0.03) 100%);
  opacity: 0;
  transition: opacity 0.25s ease;
  pointer-events: none;
}

.tab-item:hover {
  border-color: rgba(99, 102, 241, 0.35);
  color: #334155;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  box-shadow:
    0 2px 8px rgba(99, 102, 241, 0.1),
    0 1px 2px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
  transform: translateY(-1px);
}

.tab-item:hover::after {
  opacity: 1;
}

.tab-item.is-active {
  background: linear-gradient(135deg, #6366f1 0%, #5b21b6 100%);
  border-color: transparent;
  color: #fff;
  box-shadow:
    0 2px 8px rgba(99, 102, 241, 0.4),
    0 1px 3px rgba(99, 102, 241, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transform: translateY(0);
}

.tab-item.is-active::before {
  width: calc(100% - 16px);
  left: 8px;
  background: rgba(255, 255, 255, 0.5);
}

.tab-item.is-active::after {
  display: none;
}

.tab-icon {
  opacity: 0.7;
  flex-shrink: 0;
  transition: opacity 0.25s ease, transform 0.25s var(--tabs-ease);
}

.tab-item:hover .tab-icon {
  opacity: 0.95;
  transform: scale(1.08);
}

.tab-item.is-active .tab-icon {
  opacity: 1;
  color: #fff;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

.tab-title {
  max-width: 128px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.3;
}

.tab-close {
  opacity: 0;
  padding: 2px;
  border-radius: 4px;
  transition: opacity 0.2s ease, transform 0.2s var(--tabs-ease), background 0.2s ease;
  margin-left: 2px;
  flex-shrink: 0;
}

.tab-item:hover .tab-close {
  opacity: 0.65;
}

.tab-close:hover {
  opacity: 1 !important;
  background: rgba(0, 0, 0, 0.12);
  transform: scale(1.15) rotate(90deg);
}

.tab-item.is-active .tab-close {
  opacity: 0.85;
  color: #fff;
}

.tab-item.is-active .tab-close:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.28);
  transform: scale(1.15) rotate(90deg);
}

.tabs-actions {
  display: flex;
  align-items: center;
  padding-left: 8px;
  margin-left: 4px;
  border-left: 1px solid rgba(226, 232, 240, 0.7);
  flex-shrink: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
  border: 1px solid rgba(226, 232, 240, 0.8);
  transition: all 0.2s var(--tabs-ease-out);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.action-btn:hover {
  color: #6366f1;
  border-color: rgba(99, 102, 241, 0.4);
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.15);
  transform: scale(1.05);
}

/* Context Menu */
.context-menu {
  position: fixed;
  z-index: 9999;
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 12px;
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.12),
    0 4px 16px rgba(0, 0, 0, 0.06),
    0 0 0 1px rgba(0, 0, 0, 0.04);
  padding: 8px;
  min-width: 180px;
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  cursor: pointer;
  font-size: 13px;
  color: #475569;
  border-radius: 8px;
  transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
  font-weight: 500;
  letter-spacing: 0.01em;
}

.context-menu-item:hover {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.06) 100%);
  color: #6366f1;
  transform: translateX(4px);
  box-shadow: 0 1px 4px rgba(99, 102, 241, 0.12);
}

.context-menu-item .el-icon {
  font-size: 15px;
  opacity: 0.8;
  transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.context-menu-item:hover .el-icon {
  opacity: 1;
  transform: scale(1.12);
}

.context-menu-item--danger:hover {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(220, 38, 38, 0.08) 100%);
  color: #dc2626;
  box-shadow: 0 1px 4px rgba(239, 68, 68, 0.15);
}

.context-menu-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(226, 232, 240, 0.9) 50%, transparent 100%);
  margin: 6px 10px;
}

/* Context menu animation */
.context-menu-fade-enter-active {
  transition: opacity 0.2s cubic-bezier(0.22, 1, 0.36, 1), transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.context-menu-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.context-menu-fade-enter-from,
.context-menu-fade-leave-to {
  opacity: 0;
  transform: scale(0.94) translateY(-6px);
}
.context-menu-fade-enter-to {
  opacity: 1;
  transform: scale(1) translateY(0);
}

:deep(.el-dropdown-menu) {
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12), 0 4px 16px rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  padding: 8px;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  padding: 9px 14px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
}

:deep(.el-dropdown-menu__item:hover) {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.06) 100%);
  color: #6366f1;
  transform: translateX(4px);
}

:deep(.el-dropdown-menu__item .el-icon) {
  font-size: 15px;
  color: #6366f1;
  opacity: 0.85;
  transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
}

:deep(.el-dropdown-menu__item:hover .el-icon) {
  opacity: 1;
  transform: scale(1.12);
}

/* Responsive */
@media (max-width: 768px) {
  .tabs-nav {
    height: 32px;
    min-height: 32px;
    padding: 0 6px;
    gap: 2px;
  }

  .nav-arrow {
    width: 24px;
    height: 24px;
  }

  .nav-arrow .el-icon {
    font-size: 12px;
  }

  .tab-title {
    max-width: 80px;
  }

  .tab-item {
    padding: 4px 10px;
    font-size: 11px;
    gap: 5px;
  }

  .tabs-wrapper {
    padding: 4px 2px;
    gap: 4px;
  }

  .action-btn {
    width: 24px;
    height: 24px;
  }
}
</style>
