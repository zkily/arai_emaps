<template>
  <div class="metric-page">
    <header class="metric-header">
      <div class="metric-header__main">
        <div class="metric-header__icon" :style="{ background: config.gradient }">
          <el-icon :size="24"><component :is="config.icon" /></el-icon>
        </div>
        <div>
          <h1 class="metric-header__title">{{ config.title }}</h1>
          <p class="metric-header__desc">{{ config.description }}</p>
        </div>
      </div>
      <el-tag effect="light" type="info" round>生産指標</el-tag>
    </header>

    <el-card class="metric-card" shadow="hover">
      <div class="filter-row">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="～"
          start-placeholder="開始日"
          end-placeholder="終了日"
          value-format="YYYY-MM-DD"
          size="small"
          class="date-range"
        />
        <el-select v-model="process" placeholder="工程" size="small" class="process-select" clearable>
          <el-option label="全工程" value="" />
          <el-option v-for="item in processOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button type="primary" size="small" :icon="Search" @click="handleSearch">検索</el-button>
      </div>

      <div class="summary-grid">
        <div v-for="item in config.summaryCards" :key="item.label" class="summary-card">
          <div class="summary-card__label">{{ item.label }}</div>
          <div class="summary-card__value">{{ item.value }}</div>
          <div class="summary-card__sub">{{ item.sub }}</div>
        </div>
      </div>

      <section class="panel">
        <div class="panel-head">
          <span class="panel-head__mark" />
          <span class="panel-head__title">指標定義</span>
        </div>
        <div class="definition-box">
          <div class="definition-box__formula">{{ config.formula }}</div>
          <p class="definition-box__note">{{ config.note }}</p>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <span class="panel-head__mark panel-head__mark--accent" />
          <span class="panel-head__title">分析軸</span>
        </div>
        <el-table :data="config.analysisRows" size="small" border stripe class="metric-table">
          <el-table-column prop="axis" label="分析軸" width="160" />
          <el-table-column prop="content" label="内容" min-width="240" show-overflow-tooltip />
          <el-table-column prop="source" label="想定データ" min-width="220" show-overflow-tooltip />
        </el-table>
      </section>

      <section class="panel panel--muted">
        <div class="panel-head">
          <span class="panel-head__mark panel-head__mark--muted" />
          <span class="panel-head__title">実装メモ</span>
        </div>
        <ul class="memo-list">
          <li v-for="memo in config.implementationMemos" :key="memo">{{ memo }}</li>
        </ul>
      </section>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { ProductionMetricConfig } from '../types'

defineProps<{
  config: ProductionMetricConfig
}>()

const today = new Date()
const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
const formatDate = (date: Date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const dateRange = ref<[string, string]>([formatDate(firstDay), formatDate(today)])
const process = ref('')

const processOptions = [
  { label: '切断', value: 'cutting' },
  { label: '面取', value: 'chamfering' },
  { label: '成型', value: 'molding' },
  { label: '溶接', value: 'welding' },
  { label: '検査', value: 'inspection' },
]

const handleSearch = () => {
  ElMessage.info('データ取得 API 接続後に検索処理を有効化します')
}
</script>

<style scoped>
.metric-page {
  min-height: 100vh;
  padding: 20px;
  background:
    radial-gradient(circle at top left, rgba(64, 158, 255, 0.18), transparent 34%),
    linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%);
}

.metric-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 20px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(12px);
}

.metric-header__main {
  display: flex;
  align-items: center;
  gap: 14px;
}

.metric-header__icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  color: #fff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
}

.metric-header__title {
  margin: 0;
  color: #1f2937;
  font-size: 1.45rem;
  font-weight: 800;
}

.metric-header__desc {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 0.88rem;
}

.metric-card {
  border: 0;
  border-radius: 18px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.date-range {
  width: 260px;
}

.process-select {
  width: 160px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.summary-card {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: linear-gradient(180deg, #fff, #f8fafc);
}

.summary-card__label {
  color: #64748b;
  font-size: 0.78rem;
  font-weight: 700;
}

.summary-card__value {
  margin-top: 8px;
  color: #111827;
  font-size: 1.65rem;
  font-weight: 800;
}

.summary-card__sub {
  margin-top: 4px;
  color: #94a3b8;
  font-size: 0.75rem;
}

.panel {
  margin-top: 16px;
}

.panel--muted {
  padding: 14px;
  border-radius: 14px;
  background: #f8fafc;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.panel-head__mark {
  width: 4px;
  height: 16px;
  border-radius: 999px;
  background: #409eff;
}

.panel-head__mark--accent {
  background: #67c23a;
}

.panel-head__mark--muted {
  background: #909399;
}

.panel-head__title {
  color: #334155;
  font-size: 0.92rem;
  font-weight: 800;
}

.definition-box {
  padding: 14px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: #eff6ff;
}

.definition-box__formula {
  color: #1d4ed8;
  font-size: 1rem;
  font-weight: 800;
}

.definition-box__note {
  margin: 8px 0 0;
  color: #475569;
  font-size: 0.84rem;
  line-height: 1.6;
}

.metric-table {
  width: 100%;
}

.memo-list {
  margin: 0;
  padding-left: 18px;
  color: #475569;
  font-size: 0.84rem;
  line-height: 1.7;
}

@media (max-width: 768px) {
  .metric-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .date-range,
  .process-select {
    width: 100%;
  }
}
</style>
