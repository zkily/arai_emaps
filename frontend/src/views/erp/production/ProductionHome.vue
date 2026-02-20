<template>
  <div class="production-home">
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
            <el-icon size="32"><Setting /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">生産管理</h1>
            <div class="header-subtitle">Production Control</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 統計カード -->
    <div class="stats-grid">
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

    <!-- 1. 生産計画 -->
    <div class="section-title">生産計画</div>
    <div class="module-grid">
      <router-link v-for="m in planningModules" :key="m.path" :to="m.path" class="module-card modern-card">
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

    <!-- 2. 生産指示（instruction 配下の各工程） -->
    <div class="section-title">生産指示</div>
    <div class="module-grid">
      <router-link v-for="m in instructionModules" :key="m.path" :to="m.path" class="module-card modern-card">
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

    <!-- 3. 生産実績 -->
    <div class="section-title">生産実績</div>
    <div class="module-grid">
      <router-link v-for="m in resultModules" :key="m.path" :to="m.path" class="module-card modern-card">
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
  Setting, ArrowRight, Document, DataAnalysis, Tickets,
  Cpu, TrendCharts, DataLine, Calendar, CircleCheck, Operation, Connection
} from '@element-plus/icons-vue'

interface ModuleItem {
  path: string
  title: string
  description: string
  icon: Component
  gradient: string
}

const statsCards = ref([
  { key: 'active_orders', label: '製造オーダー(稼働中)', value: '24', gradient: 'linear-gradient(135deg, #409eff, #67c23a)', icon: markRaw(Document) },
  { key: 'mrp_pending', label: 'MRP未処理', value: '8', gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)', icon: markRaw(Cpu) },
  { key: 'eco_pending', label: 'ECO承認待ち', value: '3', gradient: 'linear-gradient(135deg, #f56c6c, #ff7875)', icon: markRaw(Tickets) },
  { key: 'completion_rate', label: '今月完了率', value: '87.5%', gradient: 'linear-gradient(135deg, #67c23a, #85ce61)', icon: markRaw(TrendCharts) },
])

const planningModules = ref<ModuleItem[]>([
  { path: '/erp/production/data-management', title: '生産データ管理', description: '日別生産サマリ・実績入力・進捗可視化', icon: markRaw(DataLine), gradient: 'linear-gradient(135deg, #409eff, #67c23a)' },
  { path: '/erp/production/plan-baseline', title: '計画ベースライン', description: 'ベースライン登録・計画 vs 実績比較', icon: markRaw(Calendar), gradient: 'linear-gradient(135deg, #667eea, #764ba2)' },
])

const instructionModules = ref<ModuleItem[]>([
  { path: '/erp/production/instruction/cutting', title: '切断指示', description: '切断工程の指示・実績', icon: markRaw(Operation), gradient: 'linear-gradient(135deg, #409eff, #66b1ff)' },
  { path: '/erp/production/instruction/surface', title: '面取指示', description: '面取工程の指示・実績', icon: markRaw(Operation), gradient: 'linear-gradient(135deg, #67c23a, #85ce61)' },
  { path: '/erp/production/instruction/forming', title: '成型指示', description: '成型工程の指示・実績', icon: markRaw(Operation), gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)' },
  { path: '/erp/production/instruction/welding', title: '溶接指示', description: '溶接工程の指示・実績', icon: markRaw(Connection), gradient: 'linear-gradient(135deg, #f56c6c, #ff7875)' },
  { path: '/erp/production/instruction/plating', title: 'メッキ指示', description: 'メッキ工程の指示・実績', icon: markRaw(Operation), gradient: 'linear-gradient(135deg, #909399, #b1b3b8)' },
])

const resultModules = ref<ModuleItem[]>([
  { path: '/erp/production/actual-management', title: '生産実績管理', description: '実績一覧・進捗・集計・分析', icon: markRaw(TrendCharts), gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
  { path: '/erp/production/completion', title: '完成報告', description: '製品入庫登録・歩留まり記録・品質データ連携', icon: markRaw(CircleCheck), gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
  { path: '/erp/production/consumption', title: '材料消費実績', description: 'バックフラッシュ/実消費選択・差異管理', icon: markRaw(DataAnalysis), gradient: 'linear-gradient(135deg, #a18cd1, #fbc2eb)' },
])
</script>

<style scoped>
.production-home {
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
