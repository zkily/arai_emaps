<template>
  <div class="part-home">
    <!-- 動的背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- ページヘッダー -->
    <div class="modern-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="32"><Box /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">部品管理</h1>
            <div class="header-subtitle">Parts Management</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 統計カード（オプション） -->
    <div class="stats-grid" v-if="statsCards.length">
      <div class="stat-card modern-card" v-for="stat in statsCards" :key="stat.key">
        <div class="stat-icon" :style="{ background: stat.gradient }">
          <el-icon :size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ stat.value }}</div>
        </div>
      </div>
    </div>

    <!-- 受入管理 -->
    <template v-if="receivingModules.length">
      <div class="section-title">受入管理</div>
      <div class="module-grid">
        <router-link v-for="m in receivingModules" :key="m.path" :to="m.path" class="module-card modern-card">
          <div class="module-icon" :style="{ background: m.gradient }">
            <el-icon :size="32"><component :is="m.icon" /></el-icon>
          </div>
          <div class="module-info">
            <h3 class="module-title">{{ m.title }}</h3>
            <p class="module-desc">{{ m.description }}</p>
          </div>
          <el-icon class="module-arrow"><ArrowRight /></el-icon>
        </router-link>
      </div>
    </template>

    <!-- 部品マスタ管理 -->
    <div class="section-title">部品マスタ管理</div>
    <div class="module-grid">
      <router-link v-for="m in masterModules" :key="m.path" :to="m.path" class="module-card modern-card">
        <div class="module-icon" :style="{ background: m.gradient }">
          <el-icon :size="32"><component :is="m.icon" /></el-icon>
        </div>
        <div class="module-info">
          <h3 class="module-title">{{ m.title }}</h3>
          <p class="module-desc">{{ m.description }}</p>
        </div>
        <el-icon class="module-arrow"><ArrowRight /></el-icon>
      </router-link>
    </div>

    <!-- 発注管理 -->
    <div class="section-title">発注管理</div>
    <div class="module-grid">
      <router-link v-for="m in orderModules" :key="m.path" :to="m.path" class="module-card modern-card">
        <div class="module-icon" :style="{ background: m.gradient }">
          <el-icon :size="32"><component :is="m.icon" /></el-icon>
        </div>
        <div class="module-info">
          <h3 class="module-title">{{ m.title }}</h3>
          <p class="module-desc">{{ m.description }}</p>
        </div>
        <el-icon class="module-arrow"><ArrowRight /></el-icon>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw } from 'vue'
import type { Component } from 'vue'
import {
  Box, ArrowRight, Download,
  Tickets, ShoppingCart,
} from '@element-plus/icons-vue'

interface ModuleItem {
  path: string
  title: string
  description: string
  icon: Component
  gradient: string
}

const statsCards = ref<{ key: string; label: string; value: string; gradient: string; icon: Component }[]>([])

const receivingModules = ref<ModuleItem[]>([])

const masterModules = ref<ModuleItem[]>([
  {
    path: '/master/part',
    title: '部品マスタ',
    description: '部品マスタの登録・編集（単価・仕入先等）',
    icon: markRaw(Tickets),
    gradient: 'linear-gradient(135deg, #909399, #b1b3b8)',
  },
])

const orderModules = ref<ModuleItem[]>([
  {
    path: '/erp/purchase/part/order',
    title: '部品在庫管理',
    description: '部品の在庫・発注・使用（材料在庫管理と同様の操作）',
    icon: markRaw(ShoppingCart),
    gradient: 'linear-gradient(135deg, #a18cd1, #fbc2eb)',
  },
])
</script>

<style scoped>
.part-home {
  min-height: 100vh;
  background: linear-gradient(135deg, #2d3436 0%, #636e72 100%);
  padding: 20px;
  position: relative;
}

.dynamic-background {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0; overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, rgba(255,255,255,0.03), rgba(255,255,255,0.08));
  animation: floatOrb 20s ease-in-out infinite;
}

.orb-1 { width: 300px; height: 300px; top: -100px; right: -100px; }
.orb-2 { width: 200px; height: 200px; bottom: 100px; left: -50px; animation-delay: -7s; }
.orb-3 { width: 150px; height: 150px; top: 50%; right: 20%; animation-delay: -14s; }

@keyframes floatOrb {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-30px) rotate(180deg); }
}

.modern-header {
  position: relative; z-index: 1;
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.header-content { display: flex; align-items: center; }
.header-left { display: flex; align-items: center; gap: 16px; }
.header-icon { width: 60px; height: 60px; background: rgba(255,255,255,0.15); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; }
.header-title { margin: 0; font-size: 24px; color: white; }
.header-subtitle { color: rgba(255,255,255,0.7); font-size: 14px; }

.stats-grid {
  position: relative; z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: rgba(255,255,255,0.95);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px; height: 48px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: white;
}

.stat-label { font-size: 12px; color: #909399; }
.stat-value { font-size: 20px; font-weight: bold; color: #303133; }

.section-title {
  position: relative; z-index: 1;
  font-size: 18px; font-weight: bold; color: white;
  margin: 24px 0 16px;
  padding-left: 12px;
  border-left: 4px solid rgba(255,255,255,0.5);
}

.module-grid {
  position: relative; z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.module-card {
  background: rgba(255,255,255,0.95);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
}

.module-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
}

.module-icon {
  width: 56px; height: 56px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: white;
  flex-shrink: 0;
}

.module-info { flex: 1; }
.module-title { margin: 0 0 4px; font-size: 16px; color: #303133; }
.module-desc { margin: 0; font-size: 12px; color: #909399; }
.module-arrow { color: #c0c4cc; }

@media (max-width: 1200px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .module-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .stats-grid, .module-grid { grid-template-columns: 1fr; }
}
</style>
