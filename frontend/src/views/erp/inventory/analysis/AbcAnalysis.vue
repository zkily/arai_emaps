<template>
  <div class="abc-analysis">
    <div class="page-header">
      <h2>ABC分析</h2>
      <p class="subtitle">出荷頻度・金額によるランク付け・ロケーション配置最適化</p>
    </div>

    <!-- 分析条件 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="analysisParams">
        <el-form-item label="分析基準">
          <el-select v-model="analysisParams.basis" placeholder="基準選択">
            <el-option label="出荷金額" value="amount" />
            <el-option label="出荷数量" value="quantity" />
            <el-option label="出荷回数" value="frequency" />
          </el-select>
        </el-form-item>
        <el-form-item label="分析期間">
          <el-date-picker v-model="analysisParams.dateRange" type="daterange" range-separator="〜"
            start-placeholder="開始日" end-placeholder="終了日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="倉庫">
          <el-select v-model="analysisParams.warehouse" placeholder="全て" clearable>
            <el-option v-for="w in warehouses" :key="w.cd" :label="w.name" :value="w.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="Aランク閾値">
          <el-input-number v-model="analysisParams.aThreshold" :min="50" :max="90" />%
        </el-form-item>
        <el-form-item label="Bランク閾値">
          <el-input-number v-model="analysisParams.bThreshold" :min="70" :max="99" />%
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleAnalyze"><el-icon><DataAnalysis /></el-icon> 分析実行</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- サマリー -->
    <div class="summary-section" v-if="analysisResult.total > 0">
      <div class="rank-summary">
        <el-card class="rank-card rank-a" shadow="never">
          <div class="rank-label">Aランク</div>
          <div class="rank-count">{{ analysisResult.aCount }}品目</div>
          <div class="rank-ratio">{{ analysisResult.aRatio?.toFixed(1) }}%</div>
          <div class="rank-desc">累積{{ analysisParams.aThreshold }}%以内</div>
        </el-card>
        <el-card class="rank-card rank-b" shadow="never">
          <div class="rank-label">Bランク</div>
          <div class="rank-count">{{ analysisResult.bCount }}品目</div>
          <div class="rank-ratio">{{ analysisResult.bRatio?.toFixed(1) }}%</div>
          <div class="rank-desc">累積{{ analysisParams.bThreshold }}%以内</div>
        </el-card>
        <el-card class="rank-card rank-c" shadow="never">
          <div class="rank-label">Cランク</div>
          <div class="rank-count">{{ analysisResult.cCount }}品目</div>
          <div class="rank-ratio">{{ analysisResult.cRatio?.toFixed(1) }}%</div>
          <div class="rank-desc">その他</div>
        </el-card>
      </div>
    </div>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon> エクスポート
      </el-button>
      <el-button type="success" @click="handleOptimizeLocation">
        <el-icon><Location /></el-icon> ロケーション最適化提案
      </el-button>
    </div>

    <!-- 分析結果テーブル -->
    <el-card shadow="never">
      <el-table :data="analysisItems" v-loading="loading" stripe border>
        <el-table-column prop="rank" label="ランク" width="80" align="center" fixed>
          <template #default="{ row }">
            <el-tag :type="getRankType(row.rank)" size="large">{{ row.rank }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_code" label="品番" width="120" fixed />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="category" label="カテゴリ" width="100" />
        <el-table-column prop="shipment_amount" label="出荷金額" width="120" align="right">
          <template #default="{ row }">¥{{ row.shipment_amount?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="shipment_quantity" label="出荷数量" width="100" align="right" />
        <el-table-column prop="shipment_count" label="出荷回数" width="90" align="right" />
        <el-table-column prop="cumulative_ratio" label="累積比率" width="100" align="right">
          <template #default="{ row }">{{ row.cumulative_ratio?.toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column prop="current_location" label="現ロケ" width="100" />
        <el-table-column prop="suggested_location" label="推奨ロケ" width="100">
          <template #default="{ row }">
            <span v-if="row.suggested_location !== row.current_location" class="text-primary">
              {{ row.suggested_location }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next" background />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Download, Location } from '@element-plus/icons-vue'

const loading = ref(false)
const analysisItems = ref<any[]>([])
const warehouses = ref<{ cd: string; name: string }[]>([])

const analysisParams = reactive({
  basis: 'amount',
  dateRange: null as string[] | null,
  warehouse: '',
  aThreshold: 70,
  bThreshold: 90,
})

const analysisResult = reactive({ total: 0, aCount: 0, bCount: 0, cCount: 0, aRatio: 0, bRatio: 0, cRatio: 0 })
const pagination = reactive({ page: 1, pageSize: 50, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  // TODO: API呼び出し
}

const handleAnalyze = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    ElMessage.success('ABC分析を実行しました')
  }, 1000)
}

const handleExport = () => { ElMessage.info('エクスポートしました') }
const handleOptimizeLocation = () => { ElMessage.info('ロケーション最適化提案を生成しました') }
const handleView = (row: any) => { ElMessage.info(`品番 ${row.product_code} の詳細`) }

const getRankType = (rank: string) => ({ A: 'danger', B: 'warning', C: 'info' }[rank] || 'info')
</script>

<style scoped>
.abc-analysis { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 20px; }
.summary-section { margin-bottom: 20px; }
.rank-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.rank-card { text-align: center; padding: 20px; }
.rank-card.rank-a { border-left: 4px solid #f56c6c; }
.rank-card.rank-b { border-left: 4px solid #e6a23c; }
.rank-card.rank-c { border-left: 4px solid #909399; }
.rank-label { font-size: 18px; font-weight: bold; margin-bottom: 8px; }
.rank-a .rank-label { color: #f56c6c; }
.rank-b .rank-label { color: #e6a23c; }
.rank-c .rank-label { color: #909399; }
.rank-count { font-size: 24px; font-weight: bold; }
.rank-ratio { font-size: 14px; color: #606266; margin-top: 4px; }
.rank-desc { font-size: 12px; color: #909399; margin-top: 8px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-primary { color: #409eff; font-weight: bold; }
</style>
