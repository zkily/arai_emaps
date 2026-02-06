<template>
  <div class="main-layout">
    <!-- 小屏时菜单遮罩，点击关闭菜单 -->
    <Transition name="overlay-fade">
      <div
        v-if="isMobile && !isCollapsed"
        class="layout-overlay"
        @click="isCollapsed = true"
      />
    </Transition>

    <!-- 左侧菜单 -->
    <aside class="layout-sidebar" :class="{ 'is-collapsed': isCollapsed, 'is-mobile': isMobile }">
      <SidebarMenu v-model:isCollapsed="isCollapsed" :is-mobile="isMobile" />
    </aside>

    <!-- 右侧内容区 -->
    <div class="layout-main">
      <!-- 顶部区域：头部 + 标签页 -->
      <header class="layout-header">
        <HeaderBar
          :is-mobile="isMobile"
          :sidebar-open="!isCollapsed"
          @toggle-sidebar="isCollapsed = !isCollapsed"
        />
        <TabsNav />
      </header>

      <!-- 内容区域 -->
      <main class="layout-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-slide" mode="out-in">
            <keep-alive :include="tabsStore.cachedViews">
              <component :is="Component" :key="route.path" />
            </keep-alive>
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTabsStore } from '@/stores/tabs'
import SidebarMenu from '@/components/layout/SidebarMenu.vue'
import HeaderBar from '@/components/layout/HeaderBar.vue'
import TabsNav from '@/components/layout/TabsNav.vue'

const MOBILE_BREAKPOINT = 768

const route = useRoute()
const tabsStore = useTabsStore()

const isCollapsed = ref(false)
const isMobile = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth < MOBILE_BREAKPOINT
  if (isMobile.value) {
    isCollapsed.value = true
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

watch(
  () => route.path,
  () => {
    tabsStore.addTab(route)
    if (isMobile.value) {
      isCollapsed.value = true
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: #f0f2f5;
}

.layout-sidebar {
  width: 220px;
  flex-shrink: 0;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  z-index: 20;
}

.layout-sidebar.is-collapsed {
  width: 64px;
}

.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.layout-header {
  flex-shrink: 0;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.layout-content {
  flex: 1;
  overflow: auto;
  padding: 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
}

/* 页面切换动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* 小屏下菜单遮罩 */
.layout-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 90;
}

.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.25s ease;
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

/* 小屏：侧栏为浮层 */
.layout-sidebar.is-mobile {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 100;
  box-shadow: 4px 0 16px rgba(0, 0, 0, 0.15);
}

.layout-sidebar.is-mobile.is-collapsed {
  width: 0;
  overflow: hidden;
}

/* Responsive */
@media (max-width: 768px) {
  .layout-sidebar:not(.is-mobile) {
    position: fixed;
    height: 100vh;
    z-index: 100;
  }

  .layout-sidebar.is-collapsed {
    width: 0;
  }

  .layout-content {
    padding: 8px;
  }
}
</style>
