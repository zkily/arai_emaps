<template>
  <div class="costing-home">
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
            <el-icon size="32"><Coin /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">原価・会計連携</h1>
            <div class="header-subtitle">Costing & Finance</div>
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

    <!-- 機能入口 -->
    <div class="section-title">原価管理</div>
    <div class="module-grid">
      <router-link v-for="module in costModules" :key="module.path" :to="module.path" class="module-card modern-card">
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

    <div class="section-title">固定資産管理</div>
    <div class="module-grid">
      <router-link v-for="module in assetModules" :key="module.path" :to="module.path" class="module-card modern-card">
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

    <div class="section-title">会計連携</div>
    <div class="module-grid">
      <router-link v-for="module in accountingModules" :key="module.path" :to="module.path" class="module-card modern-card">
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

    <div class="section-title">債権債務（AR/AP）</div>
    <div class="module-grid">
      <router-link v-for="module in financeModules" :key="module.path" :to="module.path" class="module-card modern-card">
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
import { ref, markRaw } from 'vue'
import { Coin, ArrowRight, Document, DataAnalysis, Money, Wallet, CreditCard } from '@element-plus/icons-vue'

const statsCards = ref([
  { key: 'variance', label: '今月原価差異', value: '¥-125,000', gradient: 'linear-gradient(135deg, #f56c6c, #f78989)', icon: markRaw(DataAnalysis) },
  { key: 'ar', label: '売掛金残高', value: '¥12,500,000', gradient: 'linear-gradient(135deg, #67c23a, #85ce61)', icon: markRaw(Wallet) },
  { key: 'ap', label: '買掛金残高', value: '¥8,200,000', gradient: 'linear-gradient(135deg, #e6a23c, #ebb563)', icon: markRaw(CreditCard) },
  { key: 'payment', label: '今月支払予定', value: '¥3,500,000', gradient: 'linear-gradient(135deg, #409eff, #66b1ff)', icon: markRaw(Money) },
])

const costModules = ref([
  { path: '/erp/costing/standard', title: '標準原価計算', description: '積み上げ計算（材料費＋加工費＋経費）', gradient: 'linear-gradient(135deg, #667eea, #764ba2)', icon: markRaw(Document) },
  { path: '/erp/costing/actual', title: '実際原価計算', description: '実績工数・実績材料費に基づく原価配賦', gradient: 'linear-gradient(135deg, #f093fb, #f5576c)', icon: markRaw(DataAnalysis) },
  { path: '/erp/costing/variance', title: '原価差異分析', description: '価格差異、数量差異、操業度差異の可視化', gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)', icon: markRaw(DataAnalysis) },
  { path: '/erp/costing/allocation', title: '配賦計算', description: '労務費・製造経費・光熱費の製品別配賦', gradient: 'linear-gradient(135deg, #a18cd1, #fbc2eb)', icon: markRaw(Money) },
  { path: '/erp/costing/wip', title: '仕掛品(WIP)評価', description: '月末時点の工程内在庫の評価額算出', gradient: 'linear-gradient(135deg, #ffecd2, #fcb69f)', icon: markRaw(DataAnalysis) },
])

const assetModules = ref([
  { path: '/erp/costing/equipment', title: '設備台帳', description: '固定資産管理・設備情報・メンテナンス履歴', gradient: 'linear-gradient(135deg, #667eea, #764ba2)', icon: markRaw(Document) },
  { path: '/erp/costing/depreciation', title: '減価償却計算', description: '定額法/定率法自動計算・製造原価連携', gradient: 'linear-gradient(135deg, #e6a23c, #ebb563)', icon: markRaw(DataAnalysis) },
])

const accountingModules = ref([
  { path: '/erp/costing/journal', title: '自動仕訳生成', description: '売上・仕入・移動・製造振替の自動仕訳', gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)', icon: markRaw(Document) },
  { path: '/erp/costing/accounting-export', title: '会計ソフト出力', description: '弥生会計・勘定奉行・freee等への出力', gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)', icon: markRaw(CreditCard) },
])

const financeModules = ref([
  { path: '/erp/costing/billing', title: '請求管理（AR）', description: '締め請求書発行、入金消込', gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)', icon: markRaw(Wallet) },
  { path: '/erp/costing/payment', title: '支払管理（AP）', description: '支払予定表作成、FBデータ出力', gradient: 'linear-gradient(135deg, #fa709a, #fee140)', icon: markRaw(CreditCard) },
])
</script>

<style scoped>
.costing-home {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  background: linear-gradient(45deg, rgba(255,255,255,0.05), rgba(255,255,255,0.1));
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
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.header-content { display: flex; align-items: center; }
.header-left { display: flex; align-items: center; gap: 16px; }
.header-icon { width: 60px; height: 60px; background: rgba(255,255,255,0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; }
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
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
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
</style>
