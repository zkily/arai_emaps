import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { RouteLocationNormalized } from 'vue-router'

const TABS_STORAGE_KEY = 'app_tabs_persist'

export interface TabItem {
  path: string
  name: string
  title: string
  query?: Record<string, any>
  params?: Record<string, any>
  closable: boolean
  icon?: string
}

const defaultTabs: TabItem[] = [
  {
    path: '/dashboard',
    name: 'Dashboard',
    title: 'ダッシュボード',
    closable: false,
    icon: 'HomeFilled'
  }
]

function loadTabsFromStorage(): { tabs: TabItem[]; activeTab: string } | null {
  try {
    const raw = localStorage.getItem(TABS_STORAGE_KEY)
    if (!raw) return null
    const data = JSON.parse(raw) as { tabs?: TabItem[]; activeTab?: string }
    if (!data?.tabs || !Array.isArray(data.tabs) || data.tabs.length === 0) return null
    const tabs = data.tabs.filter(
      (t) => t?.path && t.path !== '/login' && t.path !== ''
    ) as TabItem[]
    if (tabs.every((t) => t.path !== '/dashboard')) {
      tabs.unshift(defaultTabs[0])
    }
    const activeTab =
      typeof data.activeTab === 'string' && tabs.some((t) => t.path === data.activeTab)
        ? data.activeTab
        : tabs[0].path
    return { tabs, activeTab }
  } catch {
    return null
  }
}

function saveTabsToStorage(tabs: TabItem[], activeTab: string) {
  try {
    localStorage.setItem(
      TABS_STORAGE_KEY,
      JSON.stringify({ tabs: [...tabs], activeTab })
    )
  } catch {
    // ignore
  }
}

export const useTabsStore = defineStore('tabs', () => {
  const saved = loadTabsFromStorage()
  const tabs = ref<TabItem[]>(saved ? saved.tabs : [...defaultTabs])
  const activeTab = ref(saved ? saved.activeTab : '/dashboard')
  /** 是否刚从 localStorage 恢复，用于首次同步时导航到保存的 activeTab */
  const justRestored = ref(!!saved)

  function persist() {
    saveTabsToStorage(tabs.value, activeTab.value)
  }

  function clearJustRestored() {
    justRestored.value = false
  }
  
  // 缓存的页面名称列表（用于keep-alive）
  const cachedViews = computed(() => {
    return tabs.value.map(tab => tab.name).filter(Boolean)
  })
  
  // 添加标签页
  const addTab = (route: RouteLocationNormalized) => {
    const { path, name, meta, query, params } = route
    
    // 忽略登录页等特殊页面
    if (path === '/login' || path === '/') {
      return
    }
    
    // 检查是否已存在
    const existingTab = tabs.value.find(tab => tab.path === path)
    if (existingTab) {
      activeTab.value = path
      persist()
      return
    }
    
    // 添加新标签页
    tabs.value.push({
      path,
      name: name as string,
      title: (meta?.title as string) || '未命名',
      query: { ...query },
      params: { ...params },
      closable: path !== '/dashboard',
      icon: meta?.icon as string
    })
    
    activeTab.value = path
    persist()
  }
  
  // 关闭标签页
  const closeTab = (path: string) => {
    const index = tabs.value.findIndex(tab => tab.path === path)
    if (index === -1) return
    
    const tab = tabs.value[index]
    if (!tab.closable) return
    
    tabs.value.splice(index, 1)
    
    // 如果关闭的是当前激活的标签页，则激活相邻的标签页
    if (activeTab.value === path) {
      const nextTab = tabs.value[index] || tabs.value[index - 1]
      if (nextTab) {
        activeTab.value = nextTab.path
        persist()
        return nextTab.path
      }
    }
    persist()
    return null
  }
  
  // 关闭其他标签页
  const closeOtherTabs = (path: string) => {
    tabs.value = tabs.value.filter(tab => !tab.closable || tab.path === path)
    activeTab.value = path
    persist()
  }
  
  // 关闭所有可关闭的标签页
  const closeAllTabs = () => {
    tabs.value = tabs.value.filter(tab => !tab.closable)
    activeTab.value = tabs.value[0]?.path || '/dashboard'
    persist()
    return activeTab.value
  }
  
  // 关闭左侧标签页
  const closeLeftTabs = (path: string) => {
    const index = tabs.value.findIndex(tab => tab.path === path)
    if (index <= 0) return
    
    tabs.value = tabs.value.filter((tab, i) => !tab.closable || i >= index)
    persist()
  }
  
  // 关闭右侧标签页
  const closeRightTabs = (path: string) => {
    const index = tabs.value.findIndex(tab => tab.path === path)
    if (index === -1) return
    
    tabs.value = tabs.value.filter((tab, i) => !tab.closable || i <= index)
    persist()
  }
  
  // 设置当前激活标签页
  const setActiveTab = (path: string) => {
    activeTab.value = path
    persist()
  }
  
  // 刷新标签页（从缓存中移除再添加）
  const refreshTab = (path: string) => {
    // 这里可以触发页面刷新逻辑
    const tab = tabs.value.find(t => t.path === path)
    if (tab) {
      // 通过临时移除name来实现刷新
      const originalName = tab.name
      tab.name = ''
      setTimeout(() => {
        tab.name = originalName
      }, 100)
    }
  }
  
  return {
    tabs,
    activeTab,
    cachedViews,
    justRestored,
    clearJustRestored,
    addTab,
    closeTab,
    closeOtherTabs,
    closeAllTabs,
    closeLeftTabs,
    closeRightTabs,
    setActiveTab,
    refreshTab
  }
})
