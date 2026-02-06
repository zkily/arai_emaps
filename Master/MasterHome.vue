<template>
  <div class="master-home">
    <!-- 动态背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="40"><Setting /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="main-title">マスタ管理システム</h1>
            <p class="subtitle">各種マスタデータの管理・設定を行います</p>
          </div>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-value">{{ totalMenuItems }}</span>
            <span class="stat-label">マスタ</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ Object.keys(groupedRoutes).length }}</span>
            <span class="stat-label">カテゴリ</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-container">
      <div class="groups-container">
        <template v-if="Object.keys(groupedRoutes).length">
          <div
            v-for="(routes, group, index) in groupedRoutes"
            :key="group"
            class="group-section"
            :class="groupClass(group)"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <div class="group-header">
              <div class="group-title-wrapper">
                <div class="group-icon-wrapper">
                  <el-icon class="group-icon">
                    <component :is="getGroupIcon(group)" />
                  </el-icon>
                </div>
                <h3 class="group-title">{{ group }}</h3>
              </div>
              <div class="group-badge">{{ routes.length }}</div>
            </div>

            <div class="button-grid">
              <div
                v-for="(route, routeIndex) in routes"
                :key="route.name"
                class="button-card"
                :style="{ animationDelay: `${index * 0.1 + routeIndex * 0.05}s` }"
                @click="goTo(route.name)"
                tabindex="0"
              >
                <div class="card-background"></div>
                <div class="card-content">
                  <div class="card-icon">
                    <el-icon v-if="route.meta?.icon">
                      <component :is="route.meta.icon" />
                    </el-icon>
                    <el-icon v-else>
                      <Document />
                    </el-icon>
                  </div>
                  <div class="card-text">
                    <h4 class="card-title">{{ route.meta?.title || route.name }}</h4>
                    <p class="card-description">{{ getRouteDescription(route.name as string) }}</p>
                  </div>
                </div>
                <div class="card-arrow">
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="empty-menu">
            <el-icon size="48"><Setting /></el-icon>
            <p>利用可能なマスタがありません</p>
          </div>
        </template>
      </div>
    </div>

    <!-- 底部信息 -->
    <div class="footer-info">
      <p>© 2024 Smart Manufacturing System - Master Data Management</p>
    </div>

    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import type { RouteRecordName, RouteRecordRaw } from 'vue-router'
import {
  Setting,
  User,
  OfficeBuilding,
  Box,
  Document,
  ArrowRight,
  Tools,
  DataBoard,
  Management,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// 子ルート取得
const subRoutes = computed(() => {
  const matchedParent = route.matched.find((r) => r.path === '/master')
  return (matchedParent?.children || []).filter((r) => !!r.name) as RouteRecordRaw[]
})

// グループ毎に分類
const groupedRoutes = computed(() => {
  const groups: Record<string, RouteRecordRaw[]> = {}
  for (const r of subRoutes.value) {
    const group = (r.meta?.group as string) || 'その他'
    if (group === 'メインメニュー') continue
    if (!groups[group]) groups[group] = []
    groups[group].push(r)
  }
  return groups
})

// 总菜单项数
const totalMenuItems = computed(() => {
  return Object.values(groupedRoutes.value).reduce((total, routes) => total + routes.length, 0)
})

// グループアイコン取得
const getGroupIcon = (group: string) => {
  if (group.includes('ユーザー')) return User
  if (group.includes('取引先')) return OfficeBuilding
  if (group.includes('製品')) return Box
  if (group.includes('設備')) return Tools
  if (group.includes('工程')) return DataBoard
  return Management
}

// ルート説明取得
const getRouteDescription = (routeName: string) => {
  const descriptions: Record<string, string> = {
    UserList: 'システムユーザーの管理',
    CustomerList: '顧客情報の管理',
    SupplierList: '仕入先情報の管理',
    ProductList: '製品マスタの管理',
    MaterialList: '材料マスタの管理',
    MachineList: '設備マスタの管理',
    ProcessList: '工程マスタの管理',
  }
  return descriptions[routeName] || 'データの管理・設定'
}

// グループスタイル
const groupClass = (group: string) => {
  if (group.includes('ユーザー')) return 'group-user'
  if (group.includes('取引先')) return 'group-client'
  if (group.includes('製品')) return 'group-product'
  if (group.includes('設備')) return 'group-machine'
  if (group.includes('工程')) return 'group-process'
  return 'group-default'
}

// ルート遷移
const goTo = (routeName: RouteRecordName | undefined) => {
  if (routeName) router.replace({ name: routeName })
}
</script>

<style scoped>
.master-home {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow-x: hidden;
  scroll-behavior: smooth;
}

/* 动态背景 */
.dynamic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
  will-change: transform;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  animation: floatOrb 20s ease-in-out infinite;
  will-change: transform;
}

.orb-1 {
  width: 300px;
  height: 300px;
  top: -150px;
  right: -150px;
  animation-delay: -5s;
}

.orb-2 {
  width: 200px;
  height: 200px;
  bottom: -100px;
  left: -100px;
  animation-delay: -10s;
}

.orb-3 {
  width: 250px;
  height: 250px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -15s;
}

@keyframes floatOrb {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  33% {
    transform: translateY(-30px) rotate(120deg);
  }
  66% {
    transform: translateY(30px) rotate(240deg);
  }
}

.page-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 0 0 24px 24px;
  margin: 0 20px 30px;
  padding: 30px 40px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
  animation: iconFloat 3s ease-in-out infinite;
}

@keyframes iconFloat {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-3px);
  }
}

.header-text {
  flex: 1;
}

.main-title {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 6px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.subtitle {
  font-size: 14px;
  color: #7c8db5;
  margin: 0;
  font-weight: 500;
}

.header-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.2);
  min-width: 60px;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #667eea;
  line-height: 1;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #8492a6;
  margin-top: 4px;
  font-weight: 500;
}

/* 主要内容区域 */
.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px 40px;
  position: relative;
  z-index: 1;
}

.groups-container {
  display: grid;
  gap: 24px;
}

/* 组别区域 */
.group-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  animation: slideInUp 0.6s ease-out forwards;
  opacity: 0;
  transform: translateY(30px);
}

@keyframes slideInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.group-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

/* 组别头部 */
.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.group-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.group-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: linear-gradient(135deg, #667eea, #764ba2);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.group-icon {
  font-size: 18px;
}

.group-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #2c3e50;
}

.group-badge {
  background: linear-gradient(135deg, #e74c3c, #f39c12);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  min-width: 24px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.3);
}

/* 按钮网格 */
.button-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

/* 按钮卡片 */
.button-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
  animation: slideInCard 0.6s ease-out forwards;
  opacity: 0;
  transform: translateY(20px);
  will-change: transform;
}

.card-background {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
  transition: left 0.5s ease;
  pointer-events: none;
}

.button-card:hover .card-background {
  left: 100%;
}

@keyframes slideInCard {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.button-card:hover {
  transform: translateY(-3px);
  border-color: #667eea;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
}

.card-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.card-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  flex-shrink: 0;
}

.button-card:hover .card-icon {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.card-text {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 4px;
  color: #2c3e50;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-description {
  font-size: 12px;
  color: #8492a6;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-arrow {
  color: #bdc3c7;
  font-size: 16px;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.button-card:hover .card-arrow {
  color: #667eea;
  transform: translateX(4px);
}

/* 组别颜色主题 */
.group-user .group-icon {
  color: #3498db;
}
.group-user .group-badge {
  background: linear-gradient(135deg, #3498db, #2980b9);
}
.group-user .card-icon {
  background: linear-gradient(135deg, #3498db, #2980b9);
}

.group-client .group-icon {
  color: #27ae60;
}
.group-client .group-badge {
  background: linear-gradient(135deg, #27ae60, #229954);
}
.group-client .card-icon {
  background: linear-gradient(135deg, #27ae60, #229954);
}

.group-product .group-icon {
  color: #f39c12;
}
.group-product .group-badge {
  background: linear-gradient(135deg, #f39c12, #e67e22);
}
.group-product .card-icon {
  background: linear-gradient(135deg, #f39c12, #e67e22);
}

.group-machine .group-icon {
  color: #9b59b6;
}
.group-machine .group-badge {
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
}
.group-machine .card-icon {
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
}

.group-process .group-icon {
  color: #e74c3c;
}
.group-process .group-badge {
  background: linear-gradient(135deg, #e74c3c, #c0392b);
}
.group-process .card-icon {
  background: linear-gradient(135deg, #e74c3c, #c0392b);
}

/* 空菜单提示样式 */
.empty-menu {
  text-align: center;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 60px 40px;
  margin: 20px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-menu .el-icon {
  color: #8492a6;
}

.empty-menu p {
  color: #8492a6;
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

/* 底部信息 */
.footer-info {
  text-align: center;
  padding: 30px 20px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  font-weight: 400;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 优化滚动性能 */
* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #764ba2, #667eea);
}

/* 响应式设计优化 */
@media (max-width: 1200px) {
  .button-grid {
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  }

  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .header-stats {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 30px 15px 40px;
  }

  .main-title {
    font-size: 2rem;
    flex-direction: column;
    gap: 8px;
  }

  .subtitle {
    font-size: 1rem;
  }

  .content-container {
    padding: 0 15px 30px;
  }

  .group-section {
    padding: 24px 20px;
  }

  .button-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .button-card {
    padding: 20px;
  }

  .card-content {
    gap: 12px;
  }

  .card-icon {
    width: 45px;
    height: 45px;
    font-size: 1.3rem;
  }

  .card-title {
    font-size: 1rem;
  }

  .card-description {
    font-size: 0.85rem;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.8rem;
  }

  .group-section {
    padding: 20px 16px;
  }

  .group-title {
    font-size: 1.3rem;
  }

  .button-card {
    padding: 16px;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .group-section {
    background: rgba(45, 55, 72, 0.95);
    color: #e2e8f0;
  }

  .card-title {
    color: #e2e8f0;
  }

  .card-description {
    color: #a0aec0;
  }

  .button-card {
    background: rgba(26, 32, 44, 0.8);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .button-card:hover {
    border-color: #667eea;
  }
}
</style>
