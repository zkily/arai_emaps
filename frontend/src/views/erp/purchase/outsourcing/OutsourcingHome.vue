<template>
  <div class="outsourcing-home" :class="{ 'is-child-page': isChildPage }">
    <!-- 仅在「外注ホーム」顶层时显示：动态背景、头部、卡片区、页脚 -->
    <template v-if="!isChildPage">
      <div class="dynamic-background">
        <div class="gradient-orb orb-1"></div>
        <div class="gradient-orb orb-2"></div>
        <div class="gradient-orb orb-3"></div>
        <div class="gradient-orb orb-4"></div>
      </div>

      <div class="page-header">
        <div class="header-content">
          <div class="header-left">
            <div class="header-icon">
              <el-icon size="40">
                <OfficeBuilding />
              </el-icon>
            </div>
            <div class="header-text">
              <h1 class="main-title">外注管理システム</h1>
              <p class="subtitle">外注メッキ・溶接の注文・受入・在庫を一元管理</p>
            </div>
          </div>
          <div class="header-stats">
            <div class="stat-item">
              <span class="stat-value">{{ totalMenuItems }}</span>
              <span class="stat-label">メニュー</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ Object.keys(groupedRoutes).length }}</span>
              <span class="stat-label">グループ</span>
            </div>
          </div>
        </div>
      </div>

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
                      <el-icon v-if="route.meta?.icon" class="animated-icon">
                        <component :is="route.meta.icon" />
                      </el-icon>
                      <el-icon v-else class="animated-icon">
                        <OfficeBuilding />
                      </el-icon>
                    </div>
                    <div class="card-text">
                      <h4 class="card-title">{{ route.meta?.title || route.name }}</h4>
                      <p class="card-description">{{ getRouteDescription(route.name as string) }}</p>
                    </div>
                  </div>
                  <div class="card-arrow">
                    <el-icon>
                      <ArrowRight />
                    </el-icon>
                  </div>
                </div>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="empty-menu">
              <el-icon size="48">
                <OfficeBuilding />
              </el-icon>
              <p>暂无可用菜单</p>
            </div>
          </template>
        </div>
      </div>

      <div class="footer-info">
        <p>© 2025 Smart Manufacturing System - Outsourcing Management</p>
      </div>
    </template>

    <!-- 子路由时只显示此处；顶层时 redirect 后也会通过此处显示子页 -->
    <router-view :class="{ 'outsourcing-child-view': isChildPage }" />
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import type { RouteRecordName, RouteRecordRaw } from 'vue-router'
import {
  OfficeBuilding,
  ArrowRight,
  Document,
  Box,
  TakeawayBox,
  Goods,
  Setting,
  DataAnalysis,
  List,
  Download,
  Upload,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

/** 当前是否为子页面（ダッシュボード・外注先マスタ等），仅子页面时隐藏首页的头部/卡片/页脚 */
const isChildPage = computed(() => {
  const name = route.name as string | undefined
  if (!name) return false
  if (name === 'OutsourcingHome' || name === 'OutsourcingHomeRedirect') return false
  return true
})

const subRoutes = computed(() => {
  const matchedParent = route.matched.find((r) => r.name === 'OutsourcingHome')
  return (matchedParent?.children || []).filter((r) => !!r.name) as RouteRecordRaw[]
})

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

const getGroupIcon = (group: string) => {
  if (group.includes('注文')) return Document
  if (group.includes('受入')) return Download
  if (group.includes('支給材料')) return Upload
  if (group.includes('在庫')) return Box
  if (group.includes('使用')) return DataAnalysis
  return OfficeBuilding
}

const getRouteDescription = (routeName: string) => {
  const descriptions: Record<string, string> = {
    OutsourcingPlatingOrder: '外注メッキ加工の注文を管理',
    OutsourcingWeldingOrder: '外注溶接加工の注文を管理',
    OutsourcingPlatingReceiving: '外注メッキ品の受入処理',
    OutsourcingWeldingReceiving: '外注溶接品の受入処理',
    OutsourcingMaterialIssue: '外注業者への材料支給を管理',
    OutsourcingSuppliedMaterialStock: '外注先に支給した材料の在庫を管理',
    OutsourcingUsageManagement: '外注先での材料使用数を管理',
    OutsourcingStock: '外注品（メッキ・溶接）の在庫を一覧表示',
    OutsourcingSuppliers: '外注先マスタの登録・編集',
    OutsourcingDashboard: '外注管理の全体状況',
  }
  return descriptions[routeName] || '外注データの管理・操作'
}

const groupClass = (group: string) => {
  if (group.includes('注文')) return 'group-order'
  if (group.includes('受入')) return 'group-receiving'
  if (group.includes('支給材料')) return 'group-material'
  if (group.includes('在庫')) return 'group-stock'
  if (group.includes('使用')) return 'group-usage'
  return 'group-default'
}

const goTo = (routeName: RouteRecordName | undefined) => {
  if (routeName) router.replace({ name: routeName })
}
</script>

<style scoped>
.outsourcing-home {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #1e3c72 100%);
  position: relative;
  overflow-x: hidden;
  scroll-behavior: smooth;
}

/* 子页面时不再显示首页背景，仅保留容器让子页占满 */
.outsourcing-home.is-child-page {
  background: transparent;
  min-height: 100%;
}

.outsourcing-child-view {
  display: block;
  min-height: 100%;
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
  background: linear-gradient(45deg, rgba(30, 60, 114, 0.2), rgba(42, 82, 152, 0.15));
  animation: floatOrb 20s ease-in-out infinite;
  will-change: transform;
}

.orb-1 {
  width: 350px;
  height: 350px;
  top: -175px;
  right: -175px;
  background: linear-gradient(45deg, rgba(78, 205, 196, 0.15), rgba(30, 60, 114, 0.1));
  animation-delay: -5s;
}

.orb-2 {
  width: 250px;
  height: 250px;
  bottom: -125px;
  left: -125px;
  background: linear-gradient(45deg, rgba(255, 107, 107, 0.1), rgba(42, 82, 152, 0.15));
  animation-delay: -10s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  top: 40%;
  left: 60%;
  background: linear-gradient(45deg, rgba(67, 233, 123, 0.1), rgba(30, 60, 114, 0.15));
  animation-delay: -15s;
}

.orb-4 {
  width: 200px;
  height: 200px;
  top: 20%;
  left: 10%;
  background: linear-gradient(45deg, rgba(255, 193, 7, 0.1), rgba(42, 82, 152, 0.15));
  animation-delay: -7s;
}

@keyframes floatOrb {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  33% { transform: translateY(-40px) rotate(120deg); }
  66% { transform: translateY(40px) rotate(240deg); }
}

.page-header {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 0 0 28px 28px;
  margin: 0 16px 24px;
  padding: 24px 32px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 6px 20px rgba(30, 60, 114, 0.4);
  animation: iconFloat 3s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-4px); }
}

.header-text {
  flex: 1;
}

.main-title {
  font-size: 26px;
  font-weight: 700;
  color: #1e3c72;
  margin: 0 0 4px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.subtitle {
  font-size: 13px;
  color: #7c8db5;
  margin: 0;
  font-weight: 500;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(30, 60, 114, 0.08), rgba(42, 82, 152, 0.08));
  border-radius: 12px;
  border: 1px solid rgba(30, 60, 114, 0.15);
  min-width: 70px;
}

.stat-value {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #1e3c72;
  line-height: 1;
}

.stat-label {
  display: block;
  font-size: 11px;
  color: #8492a6;
  margin-top: 4px;
  font-weight: 500;
}

.content-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 16px 32px;
  position: relative;
  z-index: 1;
}

.groups-container {
  display: grid;
  gap: 20px;
}

.group-section {
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  animation: slideInUp 0.6s ease-out forwards;
  opacity: 0;
  transform: translateY(30px);
}

@keyframes slideInUp {
  to { opacity: 1; transform: translateY(0); }
}

.group-section:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.18);
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.group-title-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-icon-wrapper {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  box-shadow: 0 4px 12px rgba(30, 60, 114, 0.3);
}

.group-icon {
  font-size: 16px;
}

.group-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #2c3e50;
}

.group-badge {
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  color: white;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 11px;
  font-weight: 600;
  min-width: 22px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(30, 60, 114, 0.3);
}

.button-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}

.button-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.4);
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
  background: linear-gradient(90deg, transparent, rgba(30, 60, 114, 0.08), transparent);
  transition: left 0.5s ease;
  pointer-events: none;
}

.button-card:hover .card-background {
  left: 100%;
}

@keyframes slideInCard {
  to { opacity: 1; transform: translateY(0); }
}

.button-card:hover {
  transform: translateY(-4px);
  border-color: #1e3c72;
  box-shadow: 0 8px 24px rgba(30, 60, 114, 0.2);
}

.card-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(30, 60, 114, 0.3);
  flex-shrink: 0;
}

.button-card:hover .card-icon {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 6px 16px rgba(30, 60, 114, 0.4);
}

.animated-icon {
  transition: transform 0.3s ease;
}

.card-text {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 2px;
  color: #2c3e50;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-description {
  font-size: 11px;
  color: #8492a6;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-arrow {
  color: #bdc3c7;
  font-size: 14px;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.button-card:hover .card-arrow {
  color: #1e3c72;
  transform: translateX(4px);
}

/* 组别颜色主题 - 注文 */
.group-order .group-icon-wrapper {
  background: linear-gradient(135deg, #4ecdc4, #44b09e);
}
.group-order .group-badge {
  background: linear-gradient(135deg, #4ecdc4, #44b09e);
}
.group-order .card-icon {
  background: linear-gradient(135deg, #4ecdc4, #44b09e);
  box-shadow: 0 4px 12px rgba(78, 205, 196, 0.3);
}
.group-order .button-card:hover {
  border-color: #4ecdc4;
}

/* 受入 */
.group-receiving .group-icon-wrapper {
  background: linear-gradient(135deg, #667eea, #764ba2);
}
.group-receiving .group-badge {
  background: linear-gradient(135deg, #667eea, #764ba2);
}
.group-receiving .card-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
.group-receiving .button-card:hover {
  border-color: #667eea;
}

/* 支給材料 */
.group-material .group-icon-wrapper {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}
.group-material .group-badge {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}
.group-material .card-icon {
  background: linear-gradient(135deg, #f093fb, #f5576c);
  box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);
}
.group-material .button-card:hover {
  border-color: #f093fb;
}

/* 在庫 */
.group-stock .group-icon-wrapper {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}
.group-stock .group-badge {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}
.group-stock .card-icon {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
  box-shadow: 0 4px 12px rgba(67, 233, 123, 0.3);
}
.group-stock .button-card:hover {
  border-color: #43e97b;
}

/* 使用数 */
.group-usage .group-icon-wrapper {
  background: linear-gradient(135deg, #ffc107, #ff9800);
}
.group-usage .group-badge {
  background: linear-gradient(135deg, #ffc107, #ff9800);
}
.group-usage .card-icon {
  background: linear-gradient(135deg, #ffc107, #ff9800);
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
}
.group-usage .button-card:hover {
  border-color: #ffc107;
}

/* 默认 */
.group-default .group-icon-wrapper {
  background: linear-gradient(135deg, #1e3c72, #2a5298);
}
.group-default .group-badge {
  background: linear-gradient(135deg, #1e3c72, #2a5298);
}
.group-default .card-icon {
  background: linear-gradient(135deg, #1e3c72, #2a5298);
}

.footer-info {
  text-align: center;
  padding: 24px 16px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
  font-weight: 400;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 空菜单提示样式 */
.empty-menu {
  text-align: center;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 48px 32px;
  margin: 16px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-menu .el-icon {
  color: #8492a6;
}

.empty-menu p {
  color: #8492a6;
  font-size: 14px;
  font-weight: 500;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .button-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  }
  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  .header-stats {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 16px 12px;
    margin: 0 12px 16px;
  }
  .main-title { font-size: 22px; }
  .subtitle { font-size: 12px; }
  .content-container { padding: 0 12px 24px; }
  .group-section { padding: 16px; }
  .group-title { font-size: 14px; }
  .button-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  .button-card { padding: 14px; }
  .card-icon {
    width: 36px;
    height: 36px;
    font-size: 14px;
  }
  .card-title { font-size: 12px; }
  .card-description { font-size: 10px; }
}

@media (max-width: 480px) {
  .page-header {
    padding: 12px 8px;
    margin: 0 8px 12px;
  }
  .main-title { font-size: 18px; }
  .group-section { padding: 12px; }
  .button-card { padding: 12px; }
  .footer-info {
    padding: 16px 8px;
    font-size: 11px;
  }
}
</style>

