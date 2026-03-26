<template>
  <div class="inventory-home">
    <!-- 动态背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- 页面头部 -->
    <div class="modern-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="32"><Box /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">棚卸管理</h1>
            <div class="header-subtitle">Physical Inventory Management</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card modern-card" v-for="stat in statsCards" :key="stat.key">
        <div class="stat-icon" :style="{ background: stat.gradient }">
          <el-icon :size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-change" :class="stat.changeType">
            <el-icon v-if="stat.changeType === 'up'"><Top /></el-icon>
            <el-icon v-else-if="stat.changeType === 'down'"><Bottom /></el-icon>
            {{ stat.change }}
          </div>
        </div>
      </div>
    </div>

    <!-- 功能入口 -->
    <div class="module-grid">
      <router-link
        v-for="module in modules"
        :key="module.path"
        :to="module.path"
        class="module-card modern-card"
      >
        <div class="module-icon" :style="{ background: module.gradient }">
          <el-icon :size="32"><component :is="module.icon" /></el-icon>
        </div>
        <div class="module-info">
          <h3 class="module-title">{{ module.title }}</h3>
          <p class="module-desc">{{ module.description }}</p>
        </div>
        <el-icon class="module-arrow"><ArrowRight /></el-icon>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw } from 'vue'
import {
  Box,
  ArrowRight,
  Warning,
  Top,
  Bottom,
  List,
  DataAnalysis,
  Document,
  HomeFilled,
  DocumentAdd,
  Coin,
  Tools,
} from '@element-plus/icons-vue'

const modules = [
  {
    path: '/erp/inventory/stocktake',
    title: '棚卸管理ホーム',
    description: '棚卸メニュー一覧',
    icon: markRaw(HomeFilled),
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
  },
  {
    path: '/erp/inventory/stocktake/list',
    title: '棚卸リスト一覧',
    description: '棚卸データの一覧表示と管理',
    icon: markRaw(List),
    gradient: 'linear-gradient(135deg, #409eff, #67c23a)',
  },
  {
    path: '/erp/inventory/stocktake/entry',
    title: '棚卸登録',
    description: '材料、部品、ステーの実地棚卸入力',
    icon: markRaw(DocumentAdd),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)',
  },
  {
    path: '/erp/inventory/stocktake/statistics',
    title: '棚卸分析',
    description: '棚卸データの統計分析とレポート',
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #27ae60, #229954)',
  },
  {
    path: '/erp/inventory/stocktake/value',
    title: '棚卸金額管理',
    description: '在庫金額の計算・分析・レポート管理',
    icon: markRaw(Coin),
    gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
  },
  {
    path: '/erp/inventory/stocktake/carryover',
    title: '棚卸繰越管理',
    description: '月末棚卸データの翌月期初繰越',
    icon: markRaw(Tools),
    gradient: 'linear-gradient(135deg, #10b981, #059669)',
  },
]

const categoryCount = 2 // 棚卸業務 / 棚卸分析（現状のメタグループ）

const statsCards = computed(() => [
  {
    key: 'total_items',
    label: '棚卸機能数',
    value: modules.length.toLocaleString(),
    icon: markRaw(Box),
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
    change: '+0',
    changeType: 'up',
  },
  {
    key: 'total_value',
    label: 'カテゴリ数',
    value: categoryCount.toString(),
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)',
    change: '+0',
    changeType: 'up',
  },
  {
    key: 'low_stock',
    label: '登録機能',
    value: '1',
    icon: markRaw(Warning),
    gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)',
    change: '-0',
    changeType: 'down',
  },
  {
    key: 'expiring',
    label: '分析・金額',
    value: '3',
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #f56c6c, #ff7875)',
    change: '+0',
    changeType: 'up',
  },
])
</script>

<style scoped>
.inventory-home {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.dynamic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(
    45deg,
    rgba(102, 126, 234, 0.1),
    rgba(118, 75, 162, 0.1)
  );
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 300px;
  height: 300px;
  top: -150px;
  right: -150px;
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

@keyframes float {
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

.modern-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.header-title {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
}

.header-subtitle {
  font-size: 14px;
  color: #8492a6;
}

.modern-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.modern-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #8492a6;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
}

.stat-change {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
}

.stat-change.up {
  color: #67c23a;
}

.stat-change.down {
  color: #f56c6c;
}

/* 功能模块 */
.module-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.module-card {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  text-decoration: none;
  cursor: pointer;
}

.module-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.module-info {
  flex: 1;
}

.module-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 4px 0;
}

.module-desc {
  font-size: 13px;
  color: #8492a6;
  margin: 0;
}

.module-arrow {
  color: #c0c4cc;
  font-size: 20px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid,
  .module-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid,
  .module-grid {
    grid-template-columns: 1fr;
  }
}
</style>
