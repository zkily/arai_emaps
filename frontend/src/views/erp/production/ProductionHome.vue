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

    <!-- エンジニアリング -->
    <div class="section-title">エンジニアリング（基準情報）</div>
    <div class="module-grid">
      <router-link v-for="m in engineeringModules" :key="m.path" :to="m.path" class="module-card modern-card">
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

    <!-- 生産計画 -->
    <div class="section-title">生産計画（ERP側）</div>
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

    <!-- 製造指示 -->
    <div class="section-title">製造指示</div>
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

    <!-- 生産実績 -->
    <div class="section-title">生産実績（ERP側）</div>
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
import {
  Setting, ArrowRight, Document, DataAnalysis, List, Tickets,
  Connection, Box, Cpu, TrendCharts
} from '@element-plus/icons-vue'

const statsCards = ref([
  { key: 'active_orders', label: '製造オーダー(稼働中)', value: '24', gradient: 'linear-gradient(135deg, #409eff, #67c23a)', icon: markRaw(Document) },
  { key: 'mrp_pending', label: 'MRP未処理', value: '8', gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)', icon: markRaw(Cpu) },
  { key: 'eco_pending', label: 'ECO承認待ち', value: '3', gradient: 'linear-gradient(135deg, #f56c6c, #ff7875)', icon: markRaw(Tickets) },
  { key: 'completion_rate', label: '今月完了率', value: '87.5%', gradient: 'linear-gradient(135deg, #67c23a, #85ce61)', icon: markRaw(TrendCharts) },
])

const engineeringModules = ref([
  { path: '/erp/production/eco', title: '設計変更(ECO)管理', description: 'BOM版数管理・切替日設定・影響範囲分析', icon: markRaw(Document), gradient: 'linear-gradient(135deg, #667eea, #764ba2)' },
  { path: '/erp/production/bom', title: 'BOM展開', description: '正展開（構成部品検索）・逆展開（使用先検索）', icon: markRaw(Connection), gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)' },
])

const planningModules = ref([
  { path: '/erp/production/mrp', title: 'MRP（所要量計算）', description: '所要量展開・発注推奨・手配指示自動生成', icon: markRaw(Cpu), gradient: 'linear-gradient(135deg, #409eff, #67c23a)' },
  { path: '/erp/production/orders', title: '生産オーダー', description: '生産オーダー生成・進捗管理・優先順位設定', icon: markRaw(List), gradient: 'linear-gradient(135deg, #67c23a, #85ce61)' },
  { path: '/erp/production/serial', title: '製番管理', description: '個別受注生産向け：オーダー別原価管理用の番号発行', icon: markRaw(Tickets), gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)' },
])

const instructionModules = ref([
  { path: '/erp/production/work-order', title: '製造指図書', description: '現品票発行・作業指示書・工程別指示', icon: markRaw(Document), gradient: 'linear-gradient(135deg, #f093fb, #f5576c)' },
  { path: '/erp/production/material-issue', title: '材料出庫指示', description: '先入れ先出し(FIFO)・ロット指定出庫・自動引当', icon: markRaw(Box), gradient: 'linear-gradient(135deg, #fa709a, #fee140)' },
])

const resultModules = ref([
  { path: '/erp/production/completion', title: '完成報告', description: '製品入庫登録・歩留まり記録・品質データ連携', icon: markRaw(TrendCharts), gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
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
