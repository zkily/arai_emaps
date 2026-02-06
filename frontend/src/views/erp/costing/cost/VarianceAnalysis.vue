<template>
  <div class="variance-analysis">
    <div class="page-header">
      <h2>原価差異分析</h2>
      <p class="subtitle">価格差異、数量差異、操業度差異の可視化</p>
    </div>

    <!-- フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="対象期間">
          <el-date-picker v-model="filters.period" type="month" placeholder="月選択" value-format="YYYY-MM" />
        </el-form-item>
        <el-form-item label="品番">
          <el-select v-model="filters.product_code" placeholder="全て" clearable filterable>
            <el-option v-for="p in products" :key="p.cd" :label="`${p.cd} - ${p.name}`" :value="p.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="差異種別">
          <el-select v-model="filters.variance_type" placeholder="全て" clearable>
            <el-option label="価格差異" value="price" />
            <el-option label="数量差異" value="quantity" />
            <el-option label="操業度差異" value="efficiency" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleAnalyze"><el-icon><DataAnalysis /></el-icon> 分析実行</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- サマリー -->
    <div class="summary-cards">
      <el-card class="summary-card" shadow="never">
        <div class="summary-label">標準原価（合計）</div>
        <div class="summary-value">¥{{ summary.standardTotal?.toLocaleString() }}</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-label">実際原価（合計）</div>
        <div class="summary-value">¥{{ summary.actualTotal?.toLocaleString() }}</div>
      </el-card>
      <el-card class="summary-card" :class="summary.totalVariance < 0 ? 'favorable' : 'unfavorable'" shadow="never">
        <div class="summary-label">原価差異（合計）</div>
        <div class="summary-value">
          {{ summary.totalVariance >= 0 ? '+' : '' }}¥{{ summary.totalVariance?.toLocaleString() }}
        </div>
        <div class="summary-note">{{ summary.totalVariance < 0 ? '有利差異' : '不利差異' }}</div>
      </el-card>
    </div>

    <!-- 差異内訳 -->
    <el-card shadow="never" class="breakdown-card">
      <template #header>差異内訳</template>
      <div class="variance-breakdown">
        <div class="variance-item">
          <div class="variance-label">価格差異</div>
          <div class="variance-bar">
            <div class="bar" :class="summary.priceVariance < 0 ? 'favorable' : 'unfavorable'"
              :style="{ width: getBarWidth(summary.priceVariance) }"></div>
          </div>
          <div class="variance-amount" :class="summary.priceVariance < 0 ? 'text-success' : 'text-danger'">
            {{ summary.priceVariance >= 0 ? '+' : '' }}¥{{ summary.priceVariance?.toLocaleString() }}
          </div>
        </div>
        <div class="variance-item">
          <div class="variance-label">数量差異</div>
          <div class="variance-bar">
            <div class="bar" :class="summary.quantityVariance < 0 ? 'favorable' : 'unfavorable'"
              :style="{ width: getBarWidth(summary.quantityVariance) }"></div>
          </div>
          <div class="variance-amount" :class="summary.quantityVariance < 0 ? 'text-success' : 'text-danger'">
            {{ summary.quantityVariance >= 0 ? '+' : '' }}¥{{ summary.quantityVariance?.toLocaleString() }}
          </div>
        </div>
        <div class="variance-item">
          <div class="variance-label">操業度差異</div>
          <div class="variance-bar">
            <div class="bar" :class="summary.efficiencyVariance < 0 ? 'favorable' : 'unfavorable'"
              :style="{ width: getBarWidth(summary.efficiencyVariance) }"></div>
          </div>
          <div class="variance-amount" :class="summary.efficiencyVariance < 0 ? 'text-success' : 'text-danger'">
            {{ summary.efficiencyVariance >= 0 ? '+' : '' }}¥{{ summary.efficiencyVariance?.toLocaleString() }}
          </div>
        </div>
      </div>
    </el-card>

    <!-- 詳細テーブル -->
    <el-card shadow="never">
      <template #header>品目別差異詳細</template>
      <el-table :data="varianceList" v-loading="loading" stripe border>
        <el-table-column prop="product_code" label="品番" width="120" fixed />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="quantity" label="生産数" width="80" align="right" />
        <el-table-column label="標準原価" width="120" align="right">
          <template #default="{ row }">¥{{ row.standard_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="実際原価" width="120" align="right">
          <template #default="{ row }">¥{{ row.actual_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="価格差異" width="110" align="right">
          <template #default="{ row }">
            <span :class="row.price_variance < 0 ? 'text-success' : 'text-danger'">
              {{ row.price_variance >= 0 ? '+' : '' }}¥{{ row.price_variance?.toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="数量差異" width="110" align="right">
          <template #default="{ row }">
            <span :class="row.quantity_variance < 0 ? 'text-success' : 'text-danger'">
              {{ row.quantity_variance >= 0 ? '+' : '' }}¥{{ row.quantity_variance?.toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操業度差異" width="110" align="right">
          <template #default="{ row }">
            <span :class="row.efficiency_variance < 0 ? 'text-success' : 'text-danger'">
              {{ row.efficiency_variance >= 0 ? '+' : '' }}¥{{ row.efficiency_variance?.toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="合計差異" width="120" align="right">
          <template #default="{ row }">
            <span :class="row.total_variance < 0 ? 'text-success' : 'text-danger'" class="font-bold">
              {{ row.total_variance >= 0 ? '+' : '' }}¥{{ row.total_variance?.toLocaleString() }}
            </span>
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
import { DataAnalysis } from '@element-plus/icons-vue'

const loading = ref(false)
const varianceList = ref<any[]>([])
const products = ref<{ cd: string; name: string }[]>([])

const summary = reactive({
  standardTotal: 0, actualTotal: 0, totalVariance: 0,
  priceVariance: 0, quantityVariance: 0, efficiencyVariance: 0,
})
const filters = reactive({ period: '', product_code: '', variance_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { varianceList.value = [] } finally { loading.value = false }
}

const handleAnalyze = () => { ElMessage.success('差異分析を実行しました'); loadData() }

const getBarWidth = (value: number) => {
  const maxValue = Math.max(
    Math.abs(summary.priceVariance),
    Math.abs(summary.quantityVariance),
    Math.abs(summary.efficiencyVariance),
    1
  )
  return `${(Math.abs(value) / maxValue) * 100}%`
}
</script>

<style scoped>
.variance-analysis { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 20px; }
.summary-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.summary-card { text-align: center; padding: 24px; }
.summary-card.favorable { border-left: 4px solid #67c23a; }
.summary-card.unfavorable { border-left: 4px solid #f56c6c; }
.summary-label { font-size: 14px; color: #909399; margin-bottom: 8px; }
.summary-value { font-size: 28px; font-weight: bold; color: #303133; }
.summary-card.favorable .summary-value { color: #67c23a; }
.summary-card.unfavorable .summary-value { color: #f56c6c; }
.summary-note { font-size: 12px; margin-top: 4px; }
.breakdown-card { margin-bottom: 20px; }
.variance-breakdown { display: flex; flex-direction: column; gap: 16px; }
.variance-item { display: grid; grid-template-columns: 100px 1fr 120px; align-items: center; gap: 16px; }
.variance-label { font-weight: 500; }
.variance-bar { height: 24px; background: #f0f2f5; border-radius: 4px; overflow: hidden; }
.variance-bar .bar { height: 100%; border-radius: 4px; }
.variance-bar .bar.favorable { background: linear-gradient(90deg, #67c23a, #85ce61); }
.variance-bar .bar.unfavorable { background: linear-gradient(90deg, #f56c6c, #f78989); }
.variance-amount { text-align: right; font-weight: bold; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-success { color: #67c23a; }
.text-danger { color: #f56c6c; }
.font-bold { font-weight: bold; }
</style>
