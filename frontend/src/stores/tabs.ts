import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { RouteLocationNormalized } from 'vue-router'

export interface TabItem {
  path: string
  name: string
  title: string
  query?: Record<string, any>
  params?: Record<string, any>
  closable: boolean
  icon?: string
}

export const useTabsStore = defineStore('tabs', () => {
  // 已打开的标签页列表
  const tabs = ref<TabItem[]>([
    {
      path: '/dashboard',
      name: 'Dashboard',
      title: 'ダッシュボード',
      closable: false,
      icon: 'HomeFilled'
    }
  ])
  
  // 当前激活的标签页路径
  const activeTab = ref('/dashboard')
  
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
        return nextTab.path
      }
    }
    return null
  }
  
  // 关闭其他标签页
  const closeOtherTabs = (path: string) => {
    tabs.value = tabs.value.filter(tab => !tab.closable || tab.path === path)
    activeTab.value = path
  }
  
  // 关闭所有可关闭的标签页
  const closeAllTabs = () => {
    tabs.value = tabs.value.filter(tab => !tab.closable)
    activeTab.value = tabs.value[0]?.path || '/dashboard'
    return activeTab.value
  }
  
  // 关闭左侧标签页
  const closeLeftTabs = (path: string) => {
    const index = tabs.value.findIndex(tab => tab.path === path)
    if (index <= 0) return
    
    tabs.value = tabs.value.filter((tab, i) => !tab.closable || i >= index)
  }
  
  // 关闭右侧标签页
  const closeRightTabs = (path: string) => {
    const index = tabs.value.findIndex(tab => tab.path === path)
    if (index === -1) return
    
    tabs.value = tabs.value.filter((tab, i) => !tab.closable || i <= index)
  }
  
  // 设置当前激活标签页
  const setActiveTab = (path: string) => {
    activeTab.value = path
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
